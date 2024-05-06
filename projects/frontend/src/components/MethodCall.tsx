import { useState } from 'react'


// import { Provider, useWallet } from '@txnlab/use-wallet'
// import Account from './Account'

interface MethodCallInterface {
  methodFunction: () => Promise<void>           // <-- Recibe parametricamente función desde ..\frontend\src\utils\methods.ts
  text: string
}

// Este componente reotrna un elemento de botón
// este método recibe de parámetro cada uno de los métodos creados en el cliente
// y se va a encargar de inyectar un botón al frontend y hacer la llamada 
// correspondiente del servicio solicitado.
const MethodCall = ({ methodFunction, text }: MethodCallInterface) => {

    const [loading, setLoading] = useState<boolean>(false)
    const callMethodFunction = async () => {
        setLoading(true)
        await methodFunction()
        setLoading(false)
    }
  
    return (<button className='bntn m-2' onClick={callMethodFunction}>
                {loading ? <span className='loading loading-spinner'/> : text}
            </button>
            )

}


export default MethodCall
