import * as algokit from '@algorandfoundation/algokit-utils'
import { DigitalMarketplaceClient } from './contracts/DigitalMarketplace'

// This file creates 3 functions:
//     - create()
//     - buy()
//     - deleteApp()

// ############################################################################
// ########################### FUNCTION create() ##############################
// ############################################################################

export function create(
    algorand: algokit.AlgorandClient, 
    dmClient: DigitalMarketplaceClient, 
    assetBeingSold: bigint,
    unitaryPrice: bigint,
    quantity: bigint,
    sender: string,
    setAppId: (id: number) => void,
    ) {
    return async () => {
                            
        // Following line is for the user that already has an asset
        let assetId = assetBeingSold
        
        // In case of a new user that has none asset, an asset is created
        if (assetId === 0n) {

            const assetCreate = await algorand.send.assetCreate({
            sender,
            total: quantity //  <-- This is the initial ammount of asset created for the new user
            })
            
            assetId = BigInt(assetCreate.confirmation.assetIndex!)

        }

        const createResult = await dmClient.create.createApplication({
            assetId: assetBeingSold, 
            unitaryPrice
        })
        
        const mbrTxn = await algorand.transactions.payment({
            sender,
            receiver: createResult.appAddress,
            amount: algokit.algos(0.1 + 0.1),
            extraFee: algokit.algos(0.0001),
        })
        
        await dmClient.optInToAsset({ mbrPay: mbrTxn })
        
        await algorand.send.assetTransfer({
            sender,
            assetId,
            receiver : createResult.appAddress,
            amount: quantity    
        })
        
        setAppId(Number(createResult.appId))
    }
}

// ############################################################################
// ############################### FUNCTION buy() #############################
// ############################################################################

export function buy(
    algorand: algokit.AlgorandClient,  
    dmClient: DigitalMarketplaceClient,
    sender: string,
    appAddress: string,
    quantity: bigint,
    unitaryPrice: bigint,
    setUnitsLeft: (units: bigint) => void,                                           // <-- [01:12:03]
    ) {
    return async () => {
        
        const buyerTxn = await algorand.transactions.payment({
            sender,
            receiver: appAddress,
            amount: algokit.microAlgos(Number(quantity * unitaryPrice)),
            extraFee: algokit.algos(0.001),  // ????????????????????????????
        })
        
        await dmClient.buy({buyerTxn, quantity})
        
        const state = await dmClient.getGlobalState()
        const info = await algorand.account.getAssetInformation(appAddress, state.assetId!.asBigInt())

        setUnitsLeft(info.balance)       // NOTE: In the session the function called is setUnitsLeft() , with "s".
    }
}

// ############################################################################
// ############################ FUNCTION deleteApp() ##########################
// ############################################################################

export function deleteApp(
    algorand: algokit.AlgorandClient,  
    dmClient: DigitalMarketplaceClient,
    setAppId: (id: number) => void,
    ) {
    return async () => {
        await dmClient.delete.deleteApplication({})
        setAppId(0)
    }
}

