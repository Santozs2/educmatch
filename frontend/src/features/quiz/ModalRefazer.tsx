import { RefreshCw } from 'lucide-react'
import { Modal } from '../../components/Modal'
import { ButtonPrimary, ButtonSecondary } from '../../components/ui/Button'

export function ModalRefazer({ onConfirmar, onCancelar }: { onConfirmar: () => void; onCancelar: () => void }) {
  return (
    <Modal
      titulo="Refazer o teste?"
      icone={<RefreshCw className="text-red-600" size={22} />}
      onFechar={onCancelar}
      acoes={
        <>
          <ButtonPrimary onClick={onConfirmar}>Sim, refazer o teste</ButtonPrimary>
          <ButtonSecondary onClick={onCancelar}>Cancelar</ButtonSecondary>
        </>
      }
    >
      <p className="text-ink-600 text-[17px] mb-2">
        Um novo teste gera um <strong className="text-ink-900">novo resultado</strong> — este continua salvo no endereço atual.
      </p>
      <p className="text-ink-600 text-sm">Sua lista de interesse é mantida.</p>
    </Modal>
  )
}