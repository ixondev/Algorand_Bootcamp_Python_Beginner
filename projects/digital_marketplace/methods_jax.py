import algokit_utils
from algokit_utils.beta.algorand_client import (
    AlgorandClient,
    PayParams,
    AssetCreateParams, 
    AssetTransferParams,
    )

from smart_contracts.artifacts.digital_marketplace.client import DigitalMarketplaceClient

# Dispenser + AlgorandClient ⇨ Creator
# 				                    ⤷ Creator + AlgorandClient ⇨ DigitalmarketplaceClient
# 									                                        ⤷ DigitalmarketplaceClient ⇨ SmartContract

# CREACIÓN DE COMPONENTES BÁSICOS
algorand    = AlgorandClient.default_local_net() 
dispenser   = algorand.account.dispenser()
creator     = algorand.account.random()

# FONDEO DE LA CUENTA CREADORA
algorand.send.payment(
    PayParams(
        sender = dispenser.address,
        receiver = creator.address,
        amount = 10_000_000,            # Equivalente  a 10 Algos
    )
)

# CREACIÓN DEL CLIENTE DE LA APLICACIÓN
dm_client = DigitalMarketplaceClient(
    algod_client = algorand.client.algod,
    sender=creator.address,
    signer=creator.signer
)

# CREAR Y DESPLEGAR LA APLICACIÓN
create_result = dm_client.create_create_application(asset_id=0, unitary_price=0)        # <-- asset_id = 0 porque es sólo para una prueba
                                                                                        # Asocio la crecaión de la aplicación a una variable para examinar su comportamiento
print(create_result.tx_info)                                                            # compruebo la crecaión de la aplicación examinando la variable


# #############################################################################
# ############################## MÉTODO create() ##############################
# #############################################################################
# Método CREAR requiere:
#   - Crear la aplicación. (l.70)
#   - Crear el asset. (l.61-68)
#   - Que el contrato haga opt-in al Asset.
#   - Que el creador envíe Assets para vender.

def create(
    algorand: AlgorandClient,
    dm_client: DigitalMarketplaceClient,    # <-- [00:43:30] el dm_client se debe pasar desde el front end, donde ha sido creado con: def algorand() -> AlgorandClient: return AlgorandClient.default.local.net()  (ver tests)
    sender: str,                            # <-- [00:44:10] es diferente al concepto de tests
    unitary_price: int,
    quantity: int,
    asset_being_sold: int,
    set_app_id: callable                    # <-- [00:56:30]
) -> None:
    asset_id = asset_being_sold
    if (asset_id == 0):
        asset_create_result = algorand.send.asset_create(
        AssetCreateParams(
            sender=sender, 
            total=quantity
            )
        )
        asset_id = asset_create_result["confirmation"]["asset-index"]

    create_result = dm_client.create_create_application(asset_id=asset_id, 
                                                        unitary_price=unitary_price
                                                        )

    mbr_txn = algorand.transactions.payment(
        PayParams(
            sender=sender,
            receiver=create_result.tx_info["application-address"],
            amount=200_000,                                         # <-- Monto mínimo requerido por la transacci+ón de red Algorand (2 Algos)
            extra_fee=1_000                                         # <-- Costo interno de la transacción
        )
    )

    dm_client.opt_in_to_asset(
        mbr_pay=mbr_txn,
        transaction_parameters=algokit_utils.TransactionParameters(
            foreign_assets=[asset_id]
        ),
    )

    algorand.send.asset_transfer(
        AssetTransferParams(
            sender=sender,
            receiver=create_result.tx_info["application-address"],
            asset_id=asset_id,
            amount=quantity
        )
    )

    set_app_id(create_result.tx_info["application-index"])  # <-- [00:55:50] Función para almacnar localmente el "application-index"


# #############################################################################
# ################################ MÉTODO BUY() ###############################
# #############################################################################
# Método COMPRAR requiere:
#   - Invocar al método COBRAR.
#  (- Que el contrato haga opt-in al Asset <-- está implícito pues lo hace el usuario comprador directamente en su Pera wallet)

def buy(
    algorand: AlgorandClient,
    sender: str,                                # <-- [01:02:34] Notar que el "sender" es una billetera, por eso se especificad como string
    app_address: str,                           # <-- [01:03:13] Se le paga al SC por lo que se debe pasar la dirección del SC que se asociará al "receiver"
    quantity: int,                              # <-- [01:03:33] La cantidad la ingresa el usuario en el frontend al hacer la compra
    unitary_price: int,                         # <-- [01:03:37] El PU se define aquí de manera manual, pero también se puede obtener esa información desde el SC de manera automática
    dm_client: DigitalMarketplaceClient,        # <-- [01:04:10] Esto define el cliente con el cual se invocará al método buy() del SC
    set_units_left: callable,                   # <-- [01:08:50] Da acceso externo a la función set_units_left() para obtener el numero de assets remanentes que quedan en stock. 
) -> None:
    buyer_txn = algorand.transactions.payment(
        PayParams(
            sender=sender,
            receiver=app_address,
            amount=quantity*unitary_price,
            extra_fee=1_000
        )
    )

    state = dm_client.get_global_state()        # <-- [01:05:50] Permite generar el acceso al Global State mediante la variable "state" para obteer el "asset-id" que se utilizará a continuación.
                                                # <-- [01:06:11] NOTAR: También se podría codificar como "asset_id = dm_client.get_global_state()["asset-id"]" para asignar
                                                #                       directamente a la variable "foreign_assets" de dm_client.buy().

    dm_client.buy(
        quantity=quantity,
        buyer_txn=buyer_txn,
        transaction_parameters=algokit_utils.TransactionParameters(
            foreign_assets=[state["asset_id"]]
        )
    )

    set_units_left(algorand.account.get_asset_information(app_address, state["asset_id"])["asset-holding"]["amount"])    # <-- [01:07:05]


# #############################################################################
# ######################## MÉTODO DELETE_APPLICATION() ########################
# #############################################################################
# Acción COBRAR requiere:
#   - Invocar al método delete_aplication().

def delete_application(
    dm_client: DigitalMarketplaceClient,
    set_app_id: callable                            # <-- [01:11:12]
) -> None:
    dm_client.delete_delete_application(
        transaction_parameters=algokit_utils.TransactionParameters(
            foreign_assets=[dm_client.get_global_state()["asset_id"]],
        )
    )

    set_app_id(0)                                   # <-- [01:11:17] Cuando una aplicación tiene in ID con valor de cero quiere decir que no existe (no se ha creado o se ha borrado).




