from questionary import Choice, select
from main import AutoTx


def get_module():
    tx = AutoTx()
    result = select(
        "Select a method to get started",
        choices=[
            Choice("1) Add Date Base private key + address", tx.insert_db),
            Choice("2) Launching a blockchain repeater", tx.get_tx),
        ],
        qmark="⚙️ ",
        pointer="✅ "
    ).ask()

    result()

if __name__ == '__main__':
    get_module()
