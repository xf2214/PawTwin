import { t } from "./i18n";
import './pet-avatar.css'

export type PetAppearance = {
  name: string;
  species: 'cat' | 'dog';
  coat: 'gold' | 'gray' | 'cream' | 'black' | 'white';
  pattern: string;
  size: string;
}

const COLORS = {
  gold: { shade: '#d6a46b', coat: '#edc78f', cream: '#faedd5', mark: '#bd8a52' },
  gray: { shade: '#8e9b9b', coat: '#bec9c7', cream: '#e6ebe2', mark: '#6c8181' },
  cream: { shade: '#c5b494', coat: '#e4d8b9', cream: '#fff1d6', mark: '#a7977a' },
  black: { shade: '#45574d', coat: '#728275', cream: '#b5c0ab', mark: '#35473e' },
  white: { shade: '#bdc7b9', coat: '#f3f0e3', cream: '#fffaec', mark: '#a5b39f' },
}
const COATS = { gold: '暖橘', gray: '银灰', cream: '奶油', black: '黑色', white: '白色' }
const PATTERNS: Record<string, string> = { solid: '纯色', stripes: '条纹', spots: '斑块' }

/** Appearance comes from the saved pet profile, never from the showcase cast. */
export default function PetAvatar({ pet, small = false }: { pet: PetAppearance; small?: boolean }) {
  const color = COLORS[pet.coat] ?? COLORS.gold
  const dog = pet.species === 'dog'
  const size = ['small', 'medium', 'large'].includes(pet.size) ? pet.size : 'medium'
  const name = pet.name.trim() || t("新伙伴")
  const coat = COATS[pet.coat] ?? COATS.gold
  const pattern = PATTERNS[pet.pattern] ?? ''
  const label = t(`${name} 的${coat}${pattern}${dog ? '狗狗' : '猫咪'}像素形象`, `${name}’s ${t(coat)} ${pattern ? `${t(pattern)} ` : ''}${dog ? 'dog' : 'cat'} pixel avatar`)
  return <svg className={`pet-avatar pet-avatar--${size}${small ? ' pet-avatar--thumbnail' : ''}`} viewBox="0 0 144 156" role="img" aria-label={label}>
    <ellipse cx="72" cy="143" rx="41" ry="6" fill="#344b32" opacity=".12" />
    <g>
      {dog ? <>
        <path d="M106 116H118V112H122V100H130V96H134V104H130V116H126V124H106Z" fill={color.shade} />
        <path d="M126 100H134V108H126Z" fill={color.cream} />
      </> : <>
        <path d="M42 134H26V130H18V122H14V106H18V98H30V106H26V118H30V122H42Z" fill={color.shade} />
        <path d="M18 106H22V122H30V126H38V130H26V126H22V122H18Z" fill={color.coat} />
      </>}
      <path d="M46 94H98V102H106V118H110V130H102V138H84V130H60V138H42V130H34V118H38V102H46Z" fill={color.shade} />
      <path d="M46 102H98V110H102V126H94V134H88V126H56V134H46V126H42V110H46Z" fill={color.coat} />
      <path d="M54 106H90V114H94V126H86V130H58V126H50V114H54Z" fill={color.cream} />
      <path d="M42 128H60V138H42ZM84 128H102V138H84Z" fill={color.coat} />
      {pet.pattern === 'stripes' && <path d="M42 110H54V114H42ZM90 116H102V120H90Z" fill={color.mark} />}
      {pet.pattern === 'spots' && <path d="M92 102H100V110H104V122H96V126H88V118H84V110H92Z" fill={color.mark} />}
      {dog ? <>
        <path d="M26 40H38V44H106V40H118V44H126V54H130V86H126V98H118V104H104V108H40V104H26V98H18V86H14V54H18V44H26Z" fill={color.shade} />
        <path d="M30 44H42V48H102V44H114V50H122V58H126V82H122V94H114V100H102V104H42V100H30V94H22V82H18V58H22V50H30Z" fill={color.coat} />
        <path d="M18 44H30V50H34V66H30V90H26V98H14V94H10V86H6V62H10V50H14ZM114 44H126V50H130V62H138V86H134V94H130V98H118V90H114V66H110V50H114Z" fill={color.shade} />
        <path d="M14 54H22V62H26V82H22V90H14V82H10V62H14ZM122 54H130V62H134V82H130V90H122V82H118V62H122Z" fill={color.coat} />
      </> : <>
        <path d="M28 48V20H40V24H44V32H48V40H56V44H88V40H96V32H100V24H104V20H116V48H124V56H128V88H124V96H116V104H28V100H20V92H16V56H20V48Z" fill={color.shade} />
        <path d="M28 52H32V28H36V32H40V40H48V44H56V48H88V44H96V40H104V32H108V28H112V52H120V60H124V84H120V92H112V100H32V96H24V88H20V60H24V52Z" fill={color.coat} />
        <path d="M32 36H36V40H40V48H32ZM108 36H112V48H104V40H108Z" fill="#d8a699" />
      </>}
      {pet.pattern === 'stripes' && <path d="M60 48H66V62H60ZM76 48H82V62H76ZM22 70H34V74H22ZM110 70H122V74H110Z" fill={color.mark} />}
      {pet.pattern === 'spots' && <path d="M32 48H56V54H60V72H56V84H44V88H30V80H24V62H28V54H32Z" fill={color.mark} />}
      <path d="M52 82H92V86H102V94H94V98H50V94H42V86H52Z" fill={color.cream} />
      <path d="M40 64H48V68H52V76H48V80H40V76H36V68H40ZM96 64H104V68H108V76H104V80H96V76H92V68H96Z" fill="#35463a" />
      <path d="M40 65H44V69H40ZM96 65H100V69H96Z" fill="#fffef3" />
      <path d="M44 74H48V78H44ZM100 74H104V78H100Z" fill="#b5c698" />
      <path d="M28 82H40V86H28ZM104 82H116V86H104Z" fill="#dca69a" />
      <path d={dog ? 'M64 85H80V89H76V93H68V89H64Z' : 'M68 86H76V90H68Z'} fill={dog ? '#445345' : '#b78678'} />
      <path d="M70 91H74V95H70ZM64 95H70V97H64ZM74 95H80V97H74Z" fill="#8c7865" />
      {dog && <path d="M70 98H78V104H74V106H70Z" fill="#d8a699" />}
    </g>
  </svg>
}
