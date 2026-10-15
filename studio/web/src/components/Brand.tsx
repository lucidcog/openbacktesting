import wordmark from '../../../../docs/assets/brand/wordmark.svg'
import wordmarkWhite from '../../../../docs/assets/brand/wordmark-white.svg'
import monogram from '../../../../docs/assets/brand/monogram.svg'
import monogramWhite from '../../../../docs/assets/brand/monogram-white.svg'

export function Brand() {
  return <div className="studio-brand">
    <span className="studio-brand-mark" role="img" aria-label="OpenBacktesting">
      <img className="brand-full brand-light" src={wordmark} width="150" height="18" alt="" />
      <img className="brand-full brand-dark" src={wordmarkWhite} width="150" height="18" alt="" />
      <img className="brand-compact brand-light" src={monogram} width="31.2" height="18" alt="" />
      <img className="brand-compact brand-dark" src={monogramWhite} width="31.2" height="18" alt="" />
    </span>
    <span className="studio-brand-label">Studio</span>
  </div>
}
