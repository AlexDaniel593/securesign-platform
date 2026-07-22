import { HashTool } from "@/features/crypto/components/hash-tool"
import { KeyPairTool } from "@/features/crypto/components/key-pair-tool"
import { SignVerifyTool } from "@/features/crypto/components/sign-verify-tool"
import { EncryptDecryptTool } from "@/features/crypto/components/encrypt-decrypt-tool"

export default function CryptoPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Herramientas Crypto</h1>
        <p className="text-muted-foreground">
          Operaciones criptográficas: hash, generación de llaves, firma y cifrado
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <HashTool />
        <KeyPairTool />
        <SignVerifyTool />
        <EncryptDecryptTool />
      </div>
    </div>
  )
}
