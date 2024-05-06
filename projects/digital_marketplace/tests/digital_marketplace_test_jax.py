import algokit_utils
import algosdk
import pytest
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import (
    AlgorandClient,
    AssetCreateParams,
    AssetOptInParams,
    AssetTransferParams,
    PayParams,
)

from algosdk.atomic_transaction_composer import TransactionWithSigner

# IMPORTANTE: El contrato está contenido en DigitalMarketplaceClient [client.py: línea 454]
from smart_contracts.artifacts.digital_marketplace.client import DigitalMarketplaceClient




@pytest.fixture(scope="session")
def algorand() -> AlgorandClient:
    # Get an AlgorandClient to use throughout the tests
    return AlgorandClient.default_local_net()


@pytest.fixture(scope="session")
def dispenser(algorand: AlgorandClient) -> AddressAndSigner:
    # Get the dispenser to fund test addresses
    return algorand.account.dispenser()

# [00:30:00]
@pytest.fixture(scope="session")
def creator(
    algorand: AlgorandClient, 
    dispenser: AddressAndSigner
    ) -> AddressAndSigner:

    acct = algorand.account.random()

    algorand.send.payment(
        PayParams(
            sender=dispenser.address, 
            receiver=acct.address, 
            amount=10_000_000
            )
    )

    return acct

# [00:33:24]
@pytest.fixture(scope="session")
def test_asset_id(
    algorand: AlgorandClient,
    creator: AddressAndSigner 
    ) -> int:
    
    sent_txn = algorand.send.asset_create(
        AssetCreateParams(
            sender=creator.address, 
            total=10
            )
    )

    return sent_txn["confirmation"]["asset-index"]


# [00:28:58]
@pytest.fixture(scope="session")
def digital_marketplace_client(
    algorand: AlgorandClient, 
    creator: AddressAndSigner, 
    test_asset_id: int
    ) -> DigitalMarketplaceClient:
    
    """Instantiate an aplpication client we can use for our tests"""
    
    client = DigitalMarketplaceClient(
        algod_client=algorand.client.algod,
        sender=creator.address,
        signer=creator.signer,
    )

    client.create_create_application(asset_id=test_asset_id, unitary_price=0)

    return client


# [00:35:55]
# def test_pass(
#         digital_marketplace_client: DigitalMarketplaceClient
# ):
#     pass
# ----------------------------HASTA AQUÍ PARA CORRER LA PRIMERA PRUEBA

# [00:43:10]
def test_opt_in_to_asset(
    algorand: AlgorandClient,
    digital_marketplace_client: DigitalMarketplaceClient,
    test_asset_id: int,
    creator: AddressAndSigner,
):
    # ensure get_asset_information throws an error because the app is not yet opted in
    pytest.raises(
        algosdk.error.AlgodHTTPError,
        lambda: algorand.account.get_asset_information(
            digital_marketplace_client.app_address, 
            test_asset_id
        ),
    )

    # We need to send 100_000 uALGO for account MBR and 100_000 uALGO for ASA MBR
    mbr_pay_txn = algorand.transactions.payment(
        PayParams(
            sender=creator.address,
            receiver=digital_marketplace_client.app_address,        # <--  IMPORTANTE: El contrato está representado por digital_marketplace_client
            amount=200_000,
            # extra_fee=1_000,        # <-- Explicación en [00:56:51]
        )
    )

    # [00:58:10] 
    sp = algorand.client.algod.suggested_params()
    sp.fee = 1000 
    result = digital_marketplace_client.opt_in_to_asset(
        mbr_pay=TransactionWithSigner(txn=mbr_pay_txn, 
                                      signer=creator.signer
                                      ),
        transaction_parameters=algokit_utils.TransactionParameters(
            # We are using this asset in the contract, thus we need to tell the AVM its asset ID
            # In the near future, this will be done automatically
            foreign_assets=[test_asset_id],
            suggested_params=sp
        ),
    )

    assert result.confirmed_round

    assert (
        algorand.account.get_asset_information(
            digital_marketplace_client.app_address, 
            test_asset_id
        )["asset-holding"]["amount"] == 0
    )

def test_deposit(
    algorand: AlgorandClient,
    digital_marketplace_client: DigitalMarketplaceClient,
    test_asset_id: int,
    creator: AddressAndSigner,
):
    result = algorand.send.asset_transfer(
        AssetTransferParams(
            sender=creator.address,
            receiver=digital_marketplace_client.app_address,
            asset_id=test_asset_id,
            amount=5,
        )
    )

    assert result["confirmation"]

    assert (
        algorand.account.get_asset_information(
            digital_marketplace_client.app_address, test_asset_id
        )["asset-holding"]["amount"]
        == 5                            # [01:10:45]
    )


def test_set_price(digital_marketplace_client: DigitalMarketplaceClient):
    result = digital_marketplace_client.set_price(unitary_price= 300_000)   # [01:11:54]

    assert result.confirmed_round



def test_buy(
    algorand: AlgorandClient,
    digital_marketplace_client: DigitalMarketplaceClient,
    test_asset_id: int,
    creator: AddressAndSigner,
    dispenser: AddressAndSigner,
):
    # create new account to be the buyer
    buyer = algorand.account.random()

    # use the dispenser to fund buyer
    algorand.send.payment(
        PayParams(sender=dispenser.address, 
                  receiver=buyer.address, 
                  amount=10_000_000
        )
    )

    # opt the buyer into the asset
    algorand.send.asset_opt_in(
        AssetOptInParams(sender=buyer.address, 
                         asset_id=test_asset_id
        )
    )

    # form a transaction to buy two assets (2 * 3_300_000)
    buyer_txn = algorand.transactions.payment(
        PayParams(
            sender=buyer.address,
            receiver=digital_marketplace_client.app_address,
            amount= 3*300_000,                                  # [01:17:28]
            extra_fee=1000,                                    # [01:17:35]
        )
    )

    # [01:18:00]
    result = digital_marketplace_client.buy(
        quantity=3 ,
        buyer_txn=TransactionWithSigner(txn=buyer_txn, 
                                        signer=buyer.signer
                                        ),
        transaction_parameters=algokit_utils.TransactionParameters(
            # we need to tell the AVM about the asset the call will use
            foreign_assets=[test_asset_id],
            sender=buyer.address,
            signer=buyer.signer,
        ),
    )

    assert result.confirmed_round

    assert (algorand.account.get_asset_information(buyer.address, test_asset_id)["asset-holding"]["amount"] == 3 )  # [01:21:08]



def test_delete_application(
    algorand: AlgorandClient,
    digital_marketplace_client: DigitalMarketplaceClient,
    test_asset_id: int,
    creator: AddressAndSigner,
    dispenser: AddressAndSigner,
):
    before_call_amount = algorand.account.get_information(creator.address)["amount"]

    # [01:07:56]
    # sp = algorand.get_suggested_params()
    # sp.fee = 3_000
    # sp.flat_fee = True

    result = digital_marketplace_client.delete_delete_application(
        transaction_parameters=algokit_utils.TransactionParameters(
            # we are sending the asset in the call, so we need to tell the AVM
            foreign_assets=[test_asset_id],
        )
    )

    assert result.confirmed_round

    after_call_amount = algorand.account.get_information(creator.address)["amount"]

    assert after_call_amount - before_call_amount == (3 * 300_000) + 200_000 - 3000
    assert (
        algorand.account.get_asset_information(creator.address, test_asset_id)[
            "asset-holding"
        ]["amount"]
        == 7
    )
