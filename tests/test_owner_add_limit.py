# ethereum
from ethereum import tester as t
from ethereum.utils import sha3, privtoaddr, to_string
# standard libraries
from unittest import TestCase


class TestContract(TestCase):
    """
    run test with python -m unittest tests.test_owner_add_limit
    """

    HOMESTEAD_BLOCK = 1150000

    def __init__(self, *args, **kwargs):
        super(TestContract, self).__init__(*args, **kwargs)
        self.s = t.state()
        self.s.block.number = self.HOMESTEAD_BLOCK
        t.gas_limit = 4712388

    def test(self):
        # Create 50 accounts
        accounts = []
        keys = []
        account_count = 50
        for i in range(account_count):
            keys.append(sha3(to_string(i)))
            accounts.append(privtoaddr(keys[-1]))
            self.s.block.set_balance(accounts[-1], 10**18)
        # Create wallet
        required_accounts = 2
        constructor_parameters = (
            accounts,
            required_accounts
        )
        self.multisig_wallet = self.s.abi_contract(
            open('solidity/MultiSigWallet.sol').read(),
            language='solidity',
            constructor_parameters=constructor_parameters
        )
        # Create ABIs
        multisig_abi = self.multisig_wallet.translator
        # Should not be able to breach the maximum number of owners
        key_51 = sha3(to_string(51))
        account_51 = privtoaddr(key_51)
        add_owner_data = multisig_abi.encode("addOwner", [account_51])
        self.assertFalse(self.multisig_wallet.isOwner(account_51))
        add_owner_tx = self.multisig_wallet.submitTransaction(self.multisig_wallet.address, 0, add_owner_data,
                                                              sender=keys[0])
        include_pending = True
        exclude_executed = False
        self.assertEqual(self.multisig_wallet.getTransactionIds(0, 1, include_pending, exclude_executed),
                         [add_owner_tx])
        # Transaction is confirmed but cannot be executed due to too many owners.
        self.multisig_wallet.confirmTransaction(add_owner_tx, sender=keys[1])
        # Transaction remains pending
        self.assertEqual(self.multisig_wallet.getTransactionIds(0, 1, include_pending, exclude_executed),
                         [add_owner_tx])
