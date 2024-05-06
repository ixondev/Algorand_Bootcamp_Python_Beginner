// src/components/Home.tsx
import * as algokit from '@algorandfoundation/algokit-utils'
import { useWallet } from '@txnlab/use-wallet'
import React, { useState } from 'react'
import ConnectWallet from './components/ConnectWallet'
import * as methods from './methods'
// import Transact from './components/Transact'
import { DigitalMarketplaceClient } from './contracts/DigitalMarketplace'
import { getAlgodConfigFromViteEnvironment } from './utils/network/getAlgoClientConfigs'
import MethodCall from './components/MethodCall'

interface HomeProps {}

const Home: React.FC<HomeProps> = () => {
  
    algokit.Config.configure({ populateAppCallResources: true})     // <-- [00:27:32] Esto es provisorio

    // const [openWalletModal, setOpenWalletModal] = useState<boolean>(false)
    const [openWalletModal, setOpenWalletModal] = useState<boolean>(false)
    const [appId, setAppId] = useState<number>(0)                           // <-- [00:29:57]
    const [unitaryPrice, setUnitaryPrice] = useState<bigint>(0n)            // <-- [00:49:08]
    // const [quantity, setQuantity] = useState<bigint>(0n)                    // <-- [00:49:35] ESTÁ EN CERO
    const [quantity, setQuantity] = useState<bigint>(1n)                    // <-- [00:50:50] ESTÁ EN UNO
    const [assetId, setAssetId] = useState<bigint>(0n)                      // <-- [00:49:37]
    const [unitsLeft, setUnitsLeft] = useState<bigint>(0n)                  // <-- [01:12:03]
    const { activeAddress, signer } = useWallet()                   // <-- [00:31:00] Explicación y uso de useWallet https://github.com/TxnLab/use-wallet-js
                                                                    //                es una librería que permite la integración de todas las billeteras 
                                                                    //                dentro de Algorand.

    const toggleWalletModal = () => {
        setOpenWalletModal(!openWalletModal)
    }
 
    const algodConfig = getAlgodConfigFromViteEnvironment()                 // <-- [00:26:50] EXPLICACIÓN FUNCIONAMIENTO DEMCONFIGURACION DEL AMBIENTE LOCAL
    const algorand = algokit.AlgorandClient.fromConfig({algodConfig})       // <-- [00:NN:NN] CLIENTE DE ALGORAND
    algorand.setDefaultSigner(signer)                                       // <-- [00:40:10] EXPLICACIÓN DE USO

    const dmClient = new DigitalMarketplaceClient({                         // <-- [00:29:15] CLIENTE DE LA APLICACIÓN
        resolveBy: 'id',
        id: appId,                                                          // <-- [00:29:30] 
        sender: { addr: activeAddress!, signer }                            // <-- [00:30:26]
        }, 
        algorand.client.algod,                                              // <-- [00:39:46]
    )

  return (
        <div className="hero min-h-screen bg-teal-400">
            <div className="hero-content text-center rounded-lg p-6 max-w-md bg-white mx-auto">

                <div className="max-w-md">
                    <h1 className="text-4xl">
                        Bienvenido al <div className="font-bold">Marketplace de Assets 🙂</div>
                    </h1>
                    <p className="py-6">
                        Proyecto demo del bootcamp beginner de Algorand para desarrollo en Blockchain.
                    </p>
                

                    <div className="grid">

                        {/* <a
                        data-test-id="getting-started"
                        className="btn btn-primary m-2"
                        target="_blank"
                        href="https://github.com/algorandfoundation/algokit-cli"
                        >
                        Getting started
                        </a> */}

                        <button data-test-id="connect-wallet" className="btn m-2" onClick={toggleWalletModal}>
                        Wallet Connection
                        </button>

                        <div className="divider" />

                        <label className="label">App ID</label>
                        <input 
                        type="number" 
                        className='input input-bordered' 
                        value={appId} onChange={(e) => setAppId(e.currentTarget.valueAsNumber || 0 ) } 
                        />

                        <div className="divider" />

                        {activeAddress && appId === 0 && (
                            <div>
                                <MethodCall 
                                    methodFunction={                            // <-- [00:47:16]
                                        methods.create(
                                            algorand, 
                                            dmClient, 
                                            assetId,                            // <-- [00:48:07]
                                            unitaryPrice, 
                                            quantity,
                                            activeAddress!,
                                            setAppId,
                                        )
                                    }
                                    text="Crear Nueva Tienda"                  // <-- [00:48:33]
                                />
                            </div> 
                        )}

                        <ConnectWallet openModal={openWalletModal} closeModal={toggleWalletModal} />
                        {/* <Transact openModal={openDemoModal} setModalState={setOpenDemoModal} /> */}

                        <div className="divider" />
            
                            <div className="font-bold">
                                <h1 className="text-2xl">
                                    ⚙️⚙️⚙️⚙️
                                </h1>
                            </div>

                        <div className="divider" />

                    </div>
                </div>
            </div>
        </div>
    )
}

export default Home