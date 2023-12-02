import sys
import time
import os
import threading

from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_account import Account
from requests import get

from Log.Loging import log, inv_log
from Date_Base.DB import DateBase


class AutoTx:
    def __init__(self):
        load_dotenv()
        self.COLLECTING_WALLET = os.getenv('COLLECTING_WALLET')
        self.web3 = Web3(Web3.HTTPProvider(os.getenv('RPC')))
        self.db = DateBase('hold_wallet')
        self.hash_not = []

    def volume_calculation(self, address, gas, gas_price, flag=False, value=0):
        balance = self.web3.eth.get_balance(address)
        if not flag:
            log().info(int(balance - (gas * gas_price * 1.2)))
            return int(balance - (gas * gas_price * 1.2))
        else:
            log().info(int((balance + value) - (gas * gas_price * 1.2)))
            return int((balance + value) - (gas * gas_price * 1.2))

    @staticmethod
    def get_abi(address):
        url = (f"https://api-goerli.etherscan.io/api?module=contract"
               f"&action=getabi"
               f"&address={address}"
               f"&apikey=7VYV6JCYUCW4C4IT5UT5RNXH6Q4NH5TUB6")
        r = get(url).json()
        if r['result'] == 'Contract source code not verified':
            return None
        else:
            return r['result']

    def send_token(self, private_key: str, tx_hash, values: int, contract=False):
        global signed_tx

        def signet_(value_):
            if contract:
                nonce = self.web3.eth.get_transaction_count(address) + 1
            else:
                nonce = self.web3.eth.get_transaction_count(address)
            tx = {
                'from': address,
                'nonce': nonce,
                'to': self.COLLECTING_WALLET,
                'value': value_,
                'gasPrice': gas_price,
                'gas': 21000,
                'chainId': self.web3.eth.chain_id
            }
            return self.web3.eth.account.sign_transaction(tx, private_key)

        for i in range(10):
            flag = False
            try:
                address = Account.from_key(private_key).address
                gas = 21000
                gas_price = int(self.web3.eth.gas_price * 1.1)
                # if not contract:
                #     value = self.volume_calculation(value, address, gas, gas_price, contract)
                while True:
                    try:
                        receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                        # проверка статуса транзакции
                        if receipt:
                            if receipt['status'] == 1:
                                log().info(f' -> Транзакция выполнена,  отправляем токены tx -> {tx_hash} <-')
                                if not flag:
                                    log().info('Выполняем по факту')
                                    value = self.volume_calculation(address, gas, gas_price)
                                    signed_tx = signet_(value)
                                    flag = True
                                break
                            elif receipt['status'] == 0:
                                log().error('Транзакция завершилась неудачно')
                                return

                    except TransactionNotFound:
                        if not flag:
                            log().info('Выполняем по заранее')
                            signed_tx = signet_(self.volume_calculation(address, gas, gas_price, True, values))
                            flag = True
                        time.sleep(0.5)

                try:
                    self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    log().success(f'Токены в пути с {address} на {self.COLLECTING_WALLET}')
                    return
                except ValueError as error:
                    if str(error) == "{'code': -32000, 'message': 'INTERNAL_ERROR: nonce too low'}":
                        log().error('EROR NONCE')
                        signed_tx_ = signed_tx(self.volume_calculation(address, gas, gas_price))
                        self.web3.eth.send_raw_transaction(signed_tx_.rawTransaction)
                    else:
                        log().error(error)
            except BaseException as error:
                inv_log().error(error)
                time.sleep(2)

    def decode_(self, address_contract: str, tx: dict) -> float or int or None:
        address_contract = self.web3.to_checksum_address(address_contract)
        while True:
            try:
                tx = self.web3.eth.get_transaction(tx)
                break
            except TransactionNotFound:
                time.sleep(1)
        abi = self.get_abi(address_contract)

        if abi:
            contract = self.web3.eth.contract(address=address_contract, abi=abi)
            _, func_params = contract.decode_function_input(tx['input'])
            for _, i in func_params.items():

                if isinstance(i, int):
                    if i >= 0.0002 * 10 ** 18:
                        return i

    def checking_tx(self, all_tx):
        for _, tx_ in all_tx.items():
            for number in tx_:
                if tx_[number]['hash'] not in self.hash_not:
                    if self.get_address_db(str(tx_[number]['to'])):
                        self.hash_not.append(tx_[number]['hash'])
                        my_thread = threading.Thread(target=self.send_token,
                                                     args=(self.get_address_db(str(tx_[number]['to'])),
                                                           tx_[number]['hash'],
                                                           int(tx_[number]['value'], 16), ))
                        my_thread.start()
                    elif self.get_address_db(str(tx_[number]['from'])):
                        self.hash_not.append(tx_[number]['hash'])
                        value = self.decode_(tx_[number]["to"], tx_[number]['hash'])
                        if value:
                            my_thread = threading.Thread(target=self.send_token,
                                                         args=(self.get_address_db(str(tx_[number]['from'])),
                                                               tx_[number]['hash'],
                                                               value,
                                                               True, ))
                            my_thread.start()

    def get_tx(self):
        log().success('-------------START SCRIPT----------')
        while True:
            try:
                all_tx = self.web3.geth.txpool.content()
                all_tx = all_tx['pending']
                my_thread = threading.Thread(target=self.checking_tx, args=(all_tx, ))
                my_thread.start()
            except KeyboardInterrupt:
                log().info('Disabled the script using Ctrl+C')
                sys.exit()
            except BaseException as errors:
                log().error(errors)

    def insert_db(self):
        with open('wallet.txt', 'r', encoding='utf-8', errors='ignore') as data_:
            data_all = data_.read().splitlines()
        for private_key in data_all:
            try:
                address = Account.from_key(private_key).address
                self.db.insert_address(address.lower(), private_key)
            except BaseException:
                pass

    def get_address_db(self, address):
        result = self.db.get_address(address.lower())
        if result:
            return result.private_key


def main():
    tx = AutoTx()
    # tx.insert_db()
    tx.get_tx()
    # for _ in range(9000):
    #     new_account = Account.create()
    #     with open('wallet.txt', 'a') as prv:
    #         prv.write(f'{new_account._private_key.hex()}\n')
    #     with open('address.txt', 'a') as adr:
    #         adr.write(f'{new_account.address}\n')


if __name__ == "__main__":
    main()