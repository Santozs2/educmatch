import React, { useState, useEffect, useCallback } from 'react';
import {
  ChevronLeft,
  Check,
  AlertCircle,
  Download,
  RefreshCw,
  ArrowRight,
  BookOpen,
  MapPin,
  Phone,
  ZoomIn,
  Contrast,
  User,
  Trash2,
  List,
  X,
  UserPlus,
  BarChart2,
  Link2,
  Copy,
  CheckCircle,
  LogOut,
  Shield,
  ClipboardList,
  TrendingUp,
  Users,
  ExternalLink,
  History,
  Settings,
  ChevronDown,
  BarChart3,
  Award,
  ThumbsDown,
} from 'lucide-react';
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

// --- TYPES ---

type Screen =
  | 'welcome'
  | 'quiz'
  | 'calculating'
  | 'result'
  | 'detail'
  | 'login'
  | 'interestList'
  | 'profile'
  | 'testHistory'
  | 'adminDashboard'
  | 'survey'
  | 'surveyComplete';

interface SurveyResponse {
  answers: number[];
  submittedAt: string;
}

interface TestRecord {
  answers: number[];
  completedAt: string;
}

// --- DATA ---

const AREAS = [
  'Elétrica',
  'Eletromecânica',
  'Mecânica',
  'Mecânica Automotiva',
  'Costura',
  'Tecnologia da Informação',
  'Inteligência Artificial',
];

const COURSES = [
  { id: 1, name: 'Injeção Eletrônica Automotiva', mainArea: 'Mecânica Automotiva', hours: '160 horas', desc: 'Aprenda a diagnosticar e reparar sistemas de injeção eletrônica de veículos leves.', areas: { 'Mecânica Automotiva': 48, 'Elétrica': 33, 'Eletromecânica': 19 } },
  { id: 2, name: 'Eletricista Instalador', mainArea: 'Elétrica', hours: '200 horas', desc: 'Instalação e manutenção de redes elétricas residenciais e comerciais.', areas: { 'Elétrica': 60, 'Eletromecânica': 40 } },
  { id: 3, name: 'Manutenção Eletromecânica Industrial', mainArea: 'Eletromecânica', hours: '240 horas', desc: 'Mantenha equipamentos industriais funcionando com perfeição.', areas: { 'Eletromecânica': 50, 'Mecânica': 30, 'Elétrica': 20 } },
  { id: 4, name: 'Fundamentos de Inteligência Artificial', mainArea: 'Inteligência Artificial', hours: '120 horas', desc: 'Introdução aos conceitos e aplicações práticas de IA.', areas: { 'Inteligência Artificial': 70, 'Tecnologia da Informação': 30 } },
  { id: 5, name: 'Redes e Infraestrutura de TI', mainArea: 'Tecnologia da Informação', hours: '180 horas', desc: 'Planejamento e suporte de redes de computadores.', areas: { 'Tecnologia da Informação': 80, 'Inteligência Artificial': 20 } },
  { id: 6, name: 'Costura Industrial', mainArea: 'Costura', hours: '150 horas', desc: 'Técnicas de costura para produção em larga escala.', areas: { 'Costura': 100 } },
  { id: 7, name: 'Mecânica de Motores a Combustão', mainArea: 'Mecânica Automotiva', hours: '180 horas', desc: 'Desmontagem, avaliação e montagem de motores.', areas: { 'Mecânica Automotiva': 60, 'Mecânica': 40 } },
  { id: 8, name: 'Comandos Elétricos e CLP', mainArea: 'Elétrica', hours: '160 horas', desc: 'Automação de motores e processos industriais.', areas: { 'Elétrica': 50, 'Eletromecânica': 50 } },
  { id: 9, name: 'Modelagem e Corte de Vestuário', mainArea: 'Costura', hours: '140 horas', desc: 'Criação de moldes e preparação de tecidos.', areas: { 'Costura': 100 } },
  { id: 10, name: 'Python para Análise de Dados', mainArea: 'Tecnologia da Informação', hours: '120 horas', desc: 'Programação voltada para tratamento de dados.', areas: { 'Tecnologia da Informação': 60, 'Inteligência Artificial': 40 } },
];

const QUESTIONS = [
  {
    id: 1,
    text: "Qual tipo de tarefa te dá mais satisfação?",
    options: [
      { text: "Consertar coisas que estão quebradas" },
      { text: "Criar coisas novas do zero" },
      { text: "Organizar informações e resolver problemas lógicos" },
      { text: "Trabalhar com máquinas grandes e potentes" },
    ],
  },
  {
    id: 2,
    text: "Em qual ambiente você se imagina trabalhando?",
    options: [
      { text: "Em uma oficina ou indústria" },
      { text: "Em um escritório com computador" },
      { text: "Em um laboratório de testes" },
      { text: "Em diferentes lugares, atendendo clientes" },
    ],
  },
  {
    id: 3,
    text: "Você prefere trabalhar mais com o quê?",
    options: [
      { text: "Ferramentas manuais e peças mecânicas" },
      { text: "Fios, cabos e circuitos elétricos" },
      { text: "Tecidos, moldes e máquinas de costura" },
      { text: "Software, dados e programação" },
    ],
  },
  {
    id: 4,
    text: "Diante de um equipamento quebrado, o que você faz primeiro?",
    options: [
      { text: "Testo a parte elétrica com um multímetro" },
      { text: "Abro e inspeciono as peças mecânicas" },
      { text: "Procuro o manual ou o código de erro na internet" },
      { text: "Conecto um aparelho de diagnóstico" },
    ],
  },
  {
    id: 5,
    text: "O que mais te motiva em um trabalho?",
    options: [
      { text: "Ver o resultado físico do meu trabalho pronto" },
      { text: "Descobrir como as coisas funcionam por dentro" },
      { text: "Encontrar a solução mais eficiente para um problema" },
      { text: "Aprender uma tecnologia totalmente nova" },
    ],
  },
  {
    id: 6,
    text: "Como você prefere aprender uma coisa nova?",
    options: [
      { text: "Colocando a mão na massa imediatamente" },
      { text: "Lendo o manual e entendendo a teoria antes" },
      { text: "Assistindo a um vídeo e copiando os passos" },
      { text: "Desmontando algo para ver como é feito" },
    ],
  },
];

const SURVEY_QUESTIONS = [
  {
    id: 1,
    text: "Qual área técnica você tem mais interesse em aprender?",
    options: [
      "Elétrica / Eletromecânica",
      "Mecânica / Automotiva",
      "Tecnologia da Informação / IA",
      "Costura / Têxtil",
      "Ainda não sei",
    ],
  },
  {
    id: 2,
    text: "Você já possui alguma experiência em área técnica?",
    options: [
      "Nenhuma experiência",
      "Já fiz cursos básicos",
      "Trabalho na área há menos de 1 ano",
      "Trabalho na área há mais de 1 ano",
    ],
  },
  {
    id: 3,
    text: "Qual é sua disponibilidade para cursos?",
    options: [
      "Manhã",
      "Tarde",
      "Noite",
      "Fins de semana",
      "Totalmente online",
    ],
  },
  {
    id: 4,
    text: "O que mais te motiva a buscar uma formação técnica?",
    options: [
      "Conseguir meu primeiro emprego",
      "Melhorar meu salário atual",
      "Mudar de área profissional",
      "Empreender no meu próprio negócio",
    ],
  },
];

// Seeded demo data so the dashboard has meaningful numbers on first open
const SEEDED_INTEREST_COUNTS: Record<number, number> = {
  1: 12, 2: 8, 3: 5, 4: 15, 5: 9, 6: 3, 7: 7, 8: 4, 9: 2, 10: 11,
};

const SEEDED_SURVEY_RESPONSES: SurveyResponse[] = [
  { answers: [2, 0, 2, 0], submittedAt: '2026-09-10T09:12:00Z' },
  { answers: [2, 1, 0, 1], submittedAt: '2026-09-10T11:34:00Z' },
  { answers: [0, 0, 1, 2], submittedAt: '2026-09-11T14:05:00Z' },
  { answers: [1, 2, 2, 0], submittedAt: '2026-09-12T08:20:00Z' },
  { answers: [2, 0, 4, 3], submittedAt: '2026-09-13T16:47:00Z' },
  { answers: [3, 1, 0, 1], submittedAt: '2026-09-14T10:30:00Z' },
];

const ADMIN_EMAIL = 'admin@senai.com';
const ADMIN_PASSWORD = 'admin123';

// --- UTILITY ---

function generateToken(): string {
  return Array.from({ length: 12 }, () =>
    Math.random().toString(36).charAt(2)
  ).join('');
}

// --- SHARED COMPONENTS ---

function Header({
  hideNav = false,
  isLoggedIn = false,
  isAdmin = false,
  onLoginClick,
  onViewInterests,
  onViewProfile,
  onViewTests,
  onViewDashboard,
  onLogout,
}: {
  hideNav?: boolean;
  isLoggedIn?: boolean;
  isAdmin?: boolean;
  onLoginClick?: () => void;
  onViewInterests?: () => void;
  onViewProfile?: () => void;
  onViewTests?: () => void;
  onViewDashboard?: () => void;
  onLogout?: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <header className="bg-ink-900 text-white p-4">
      <div className="max-w-[1440px] mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className="font-bold text-xl cursor-pointer hover:text-red-100 transition-colors"
            onClick={() => window.location.reload()}
          >
            QuizPessoal
          </span>
          <span className="bg-white/20 text-white text-xs px-2 py-1 rounded-full hidden sm:inline-block">
            Orientação profissional
          </span>
        </div>
        {!hideNav && (
          <div className="flex items-center gap-2 sm:gap-4">
            <div className="hidden sm:flex gap-2 mr-2 sm:mr-4 border-r border-ink-600 pr-2 sm:pr-4">
              <button className="flex items-center gap-1 text-sm font-semibold hover:text-red-100 p-2 min-h-[48px] min-w-[48px] justify-center" aria-label="Aumentar fonte">
                A <ZoomIn size={16} />
              </button>
              <button className="flex items-center gap-1 text-sm font-semibold hover:text-red-100 p-2 min-h-[48px] min-w-[48px] justify-center" aria-label="Alto contraste">
                <Contrast size={16} />
              </button>
            </div>

            {isLoggedIn ? (
              <div className="relative">
                <button
                  onClick={() => setMenuOpen((open) => !open)}
                  aria-expanded={menuOpen}
                  aria-haspopup="menu"
                  className="flex items-center gap-2 rounded-lg border border-white/25 bg-white/10 px-3 py-2 text-sm font-bold text-white transition-colors hover:bg-white/20"
                >
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-red-600 text-xs">{isAdmin ? 'A' : 'M'}</span>
                  <span className="hidden sm:inline">{isAdmin ? 'Administração' : 'Minha conta'}</span>
                  <ChevronDown size={16} className={menuOpen ? 'rotate-180 transition-transform' : 'transition-transform'} />
                </button>
                {menuOpen && (
                  <div role="menu" className="absolute right-0 top-[calc(100%+10px)] z-40 w-60 overflow-hidden rounded-xl border border-line-200 bg-white py-2 text-ink-900 shadow-xl">
                    <button role="menuitem" onClick={() => { setMenuOpen(false); onViewInterests?.(); }} className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-semibold hover:bg-red-50"><List size={17} className="text-red-600" /> Minha lista</button>
                    <button role="menuitem" onClick={() => { setMenuOpen(false); onViewTests?.(); }} className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-semibold hover:bg-red-50"><History size={17} className="text-red-600" /> Meus testes</button>
                    <button role="menuitem" onClick={() => { setMenuOpen(false); onViewProfile?.(); }} className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm font-semibold hover:bg-red-50"><Settings size={17} className="text-red-600" /> Meu perfil</button>
                    {isAdmin && <button role="menuitem" onClick={() => { setMenuOpen(false); onViewDashboard?.(); }} className="flex w-full items-center gap-3 border-t border-line-200 px-4 py-3 text-left text-sm font-bold hover:bg-red-50"><BarChart3 size={17} className="text-red-600" /> Dashboard</button>}
                    <button role="menuitem" onClick={() => { setMenuOpen(false); onLogout?.(); }} className="flex w-full items-center gap-3 border-t border-line-200 px-4 py-3 text-left text-sm font-semibold text-ink-600 hover:bg-red-50 hover:text-red-700"><LogOut size={17} /> Sair</button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={onLoginClick}
                className="flex items-center gap-2 border-2 border-white/30 hover:bg-white/10 text-white px-4 py-2 rounded-lg font-bold transition-all duration-200 text-sm active:scale-95"
              >
                <User size={16} /> <span className="hidden sm:inline">Entrar</span>
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
}

function ButtonPrimary({ children, onClick, className = '', disabled = false, type = 'button' }: any) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`bg-red-600 hover:bg-red-700 active:bg-red-900 active:scale-[0.98] disabled:bg-ink-300 disabled:active:scale-100 disabled:opacity-70 text-white font-bold rounded-xl min-h-[56px] px-8 flex items-center justify-center transition-all duration-200 w-full shadow-sm hover:shadow-md ${className}`}
    >
      {children}
    </button>
  );
}

function ButtonSecondary({ children, onClick, className = '', type = 'button' }: any) {
  return (
    <button
      type={type}
      onClick={onClick}
      className={`bg-white border-2 border-red-600 text-red-600 hover:bg-red-50 active:bg-red-100 active:scale-[0.98] font-bold rounded-xl min-h-[56px] px-8 flex items-center justify-center transition-all duration-200 w-full shadow-sm hover:shadow-md ${className}`}
    >
      {children}
    </button>
  );
}

function ButtonGhost({ children, onClick, className = '', type = 'button' }: any) {
  return (
    <button
      type={type}
      onClick={onClick}
      className={`bg-transparent text-red-600 hover:bg-red-50 active:bg-red-100 active:scale-[0.98] font-bold rounded-xl min-h-[56px] px-8 flex items-center justify-center transition-all duration-200 w-full ${className}`}
    >
      {children}
    </button>
  );
}

// --- SCREENS ---

function WelcomeScreen({
  onStart,
  isLoggedIn,
  isAdmin,
  onLoginClick,
  onViewInterests,
  onViewProfile,
  onViewTests,
  onViewDashboard,
  onLogout,
}: {
  onStart: (name: string) => void;
  isLoggedIn: boolean;
  isAdmin: boolean;
  onLoginClick: () => void;
  onViewInterests: () => void;
  onViewProfile: () => void;
  onViewTests: () => void;
  onViewDashboard: () => void;
  onLogout: () => void;
}) {
  const [name, setName] = useState('');

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Header isLoggedIn={isLoggedIn} isAdmin={isAdmin} onLoginClick={onLoginClick} onViewInterests={onViewInterests} onViewProfile={onViewProfile} onViewTests={onViewTests} onViewDashboard={onViewDashboard} onLogout={onLogout} />
      <main className="flex-1 max-w-[1440px] w-full mx-auto p-5 sm:p-8 md:p-12 flex flex-col items-center justify-center">
        <div className="max-w-[600px] w-full bg-white rounded-[12px] p-6 sm:p-10 shadow-[0_8px_24px_rgba(16,24,40,0.08)]">
          <h1 className="text-3xl sm:text-4xl font-bold text-red-900 mb-4 leading-tight">
            Descubra o curso certo para o seu perfil
          </h1>
          <p className="text-ink-600 text-[17px] mb-8">
            Responda a 6 perguntas simples sobre o seu jeito de trabalhar e descubra as áreas que mais combinam com você.
          </p>

          <div className="flex flex-wrap gap-3 mb-8">
            <span className="bg-ink-900 text-white px-4 py-1.5 rounded-full text-sm font-semibold flex items-center gap-1 shadow-sm">
              Leva 2 minutos
            </span>
            <span className="bg-white border border-line-200 text-ink-900 px-4 py-1.5 rounded-full text-sm font-semibold flex items-center gap-1 shadow-sm">
              Sem cadastro
            </span>
            <span className="bg-white border border-line-200 text-ink-900 px-4 py-1.5 rounded-full text-sm font-semibold flex items-center gap-1 shadow-sm">
              6 perguntas
            </span>
          </div>

          <div className="mb-8">
            <label htmlFor="name" className="block font-semibold text-ink-900 mb-2">Seu nome (opcional)</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full border-2 border-line-200 rounded-[8px] p-3 min-h-[48px] text-[17px] text-ink-900 focus:border-red-600 focus:ring-0 outline-none"
            />
          </div>

          <ButtonPrimary onClick={() => onStart(name)}>Começar</ButtonPrimary>

          <p className="text-center text-ink-600 text-sm mt-4">
            Nenhum dado seu é compartilhado.
          </p>
        </div>
      </main>
    </div>
  );
}

function QuizScreen({
  questionIndex,
  answers,
  onSelect,
  onNext,
  onPrev,
}: {
  questionIndex: number;
  answers: number[];
  onSelect: (qIndex: number, oIndex: number) => void;
  onNext: () => void;
  onPrev: () => void;
}) {
  const q = QUESTIONS[questionIndex];
  const selectedIndex = answers[questionIndex];
  const [error, setError] = useState(false);

  const handleNext = () => {
    if (selectedIndex === undefined) {
      setError(true);
    } else {
      setError(false);
      onNext();
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col pb-24">
      <header className="bg-white border-b border-line-200">
        <div className="h-2 w-full bg-red-100">
          <div
            className="h-full bg-red-600 transition-all duration-300"
            style={{ width: `${((questionIndex + 1) / QUESTIONS.length) * 100}%` }}
          />
        </div>
        <div className="max-w-[1440px] mx-auto p-4 flex items-center">
          <button
            onClick={onPrev}
            className="flex items-center text-red-600 font-semibold min-h-[48px] px-2 hover:bg-red-50 rounded"
          >
            <ChevronLeft size={20} className="mr-1" /> Voltar
          </button>
          <span className="mx-auto font-semibold text-ink-600 pr-[88px] sm:pr-0">
            Pergunta {questionIndex + 1} de {QUESTIONS.length}
          </span>
        </div>
      </header>

      <main className="flex-1 max-w-[600px] w-full mx-auto p-5 sm:p-8 flex flex-col">
        {error && (
          <div className="bg-red-50 border border-red-300 rounded-lg p-4 mb-6 flex items-start gap-3 text-ink-900">
            <AlertCircle className="text-red-600 mt-0.5 shrink-0" size={20} />
            <span className="font-semibold">Escolha uma opção para continuar.</span>
          </div>
        )}

        <h2 className="text-2xl font-bold text-ink-900 mb-8 leading-tight">
          <span className="text-red-600 mr-2">{questionIndex + 1}.</span>
          {q.text}
        </h2>

        <div className="flex flex-col gap-4">
          {q.options.map((opt, idx) => {
            const isSelected = selectedIndex === idx;
            return (
              <button
                key={idx}
                onClick={() => {
                  setError(false);
                  onSelect(questionIndex, idx);
                }}
                className={`
                  flex items-center text-left p-5 rounded-xl min-h-[72px] border-2 transition-all duration-200 group
                  ${isSelected
                    ? 'border-red-600 bg-red-50 shadow-sm ring-1 ring-red-600'
                    : 'border-line-200 bg-white hover:border-red-300 hover:shadow-md hover:-translate-y-0.5'
                  }
                `}
              >
                <div className={`
                  w-8 h-8 rounded-full flex items-center justify-center shrink-0 mr-4 font-bold transition-colors
                  ${isSelected ? 'bg-red-600 text-white' : 'bg-line-200 text-ink-600 group-hover:bg-red-100 group-hover:text-red-900'}
                `}>
                  {idx + 1}
                </div>
                <span className={`flex-1 text-[17px] leading-snug ${isSelected ? 'font-bold text-red-900' : 'text-ink-900'}`}>
                  {opt.text}
                </span>
                <div className="w-6 h-6 ml-2 flex items-center justify-center shrink-0">
                  {isSelected && <Check className="text-red-600" size={24} />}
                </div>
              </button>
            );
          })}
        </div>
      </main>

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-line-200 shadow-[0_-4px_16px_rgba(0,0,0,0.05)]">
        <div className="max-w-[600px] mx-auto">
          <ButtonPrimary onClick={handleNext}>Próxima</ButtonPrimary>
        </div>
      </div>
    </div>
  );
}

function CalculatingScreen() {
  return (
    <div className="min-h-screen bg-bg-50 flex flex-col items-center justify-center p-5">
      <div className="bg-white p-10 rounded-2xl shadow-sm border border-line-200 flex flex-col items-center animate-in zoom-in-95 duration-300">
        <RefreshCw size={48} className="text-red-600 animate-spin mb-8" />
        <h2 className="text-2xl font-bold text-ink-900 text-center max-w-[320px] animate-pulse">
          Analisando seu perfil e cruzando com nossos cursos...
        </h2>
        <p className="text-ink-600 mt-4 text-sm font-medium">Isso leva só um instante</p>
      </div>
    </div>
  );
}

function ConfirmResetModal({ onConfirm, onCancel }: { onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 sm:p-8 animate-in zoom-in-95 duration-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center shrink-0">
            <RefreshCw className="text-red-600" size={22} />
          </div>
          <h2 className="text-xl font-bold text-ink-900">Refazer o teste?</h2>
        </div>
        <p className="text-ink-600 text-[17px] mb-2">
          Atenção: se você refizer o teste, <strong className="text-ink-900">suas respostas atuais serão apagadas</strong> e o resultado poderá ser completamente diferente do atual.
        </p>
        <p className="text-ink-600 text-sm mb-8">
          Sua lista de interesse será mantida mesmo ao refazer o teste.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <ButtonPrimary onClick={onConfirm}>Sim, refazer o teste</ButtonPrimary>
          <ButtonSecondary onClick={onCancel}>Cancelar</ButtonSecondary>
        </div>
      </div>
    </div>
  );
}

function ResultScreen({
  name,
  onReset,
  onViewCourse,
  isLoggedIn,
  isAdmin,
  onLoginClick,
  onViewInterests,
  onViewProfile,
  onViewTests,
  onViewDashboard,
  onLogout,
}: {
  name: string;
  onReset: () => void;
  onViewCourse: (id: number) => void;
  isLoggedIn: boolean;
  isAdmin: boolean;
  onLoginClick: () => void;
  onViewInterests: () => void;
  onViewProfile: () => void;
  onViewTests: () => void;
  onViewDashboard: () => void;
  onLogout: () => void;
}) {
  const [showResetModal, setShowResetModal] = useState(false);
  const bestMatch = COURSES[0];
  const others = COURSES.slice(1, 5);

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Header isLoggedIn={isLoggedIn} isAdmin={isAdmin} onLoginClick={onLoginClick} onViewInterests={onViewInterests} onViewProfile={onViewProfile} onViewTests={onViewTests} onViewDashboard={onViewDashboard} onLogout={onLogout} />
      <main className="flex-1 max-w-[800px] w-full mx-auto p-5 sm:p-8 flex flex-col">
        <h1 className="text-3xl font-bold text-red-900 mb-6 leading-tight">
          {name ? `${name}, esses` : 'Esses'} são os cursos que mais combinam com você
        </h1>

        <div className="bg-white rounded-2xl border-2 border-ink-900 overflow-hidden mb-10 shadow-lg transition-all hover:shadow-xl">
          <div className="bg-ink-900 p-3 flex items-center justify-center border-b-2 border-ink-900">
            <span className="bg-white text-ink-900 font-bold px-4 py-1 rounded-full uppercase text-sm tracking-wide flex items-center gap-2">
              <Check size={16} className="text-red-600" /> Melhor combinação
            </span>
          </div>

          <div className="p-6 sm:p-8 flex flex-col sm:flex-row gap-8 items-center sm:items-start">
            <div className="flex flex-col items-center shrink-0">
              <div className="relative w-[140px] h-[140px] flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90 drop-shadow-sm" viewBox="0 0 140 140">
                  <circle cx="70" cy="70" r="58" fill="transparent" stroke="var(--color-line-200)" strokeWidth="12" />
                  <circle cx="70" cy="70" r="58" fill="transparent" stroke="var(--color-red-600)" strokeWidth="12" strokeDasharray="364.4" strokeDashoffset="14.5" className="transition-all duration-1000 ease-out animate-in fade-in zoom-in" strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-white rounded-full m-[12px] shadow-[inset_0_2px_4px_rgba(0,0,0,0.06)]">
                  <span className="text-4xl font-bold text-ink-900 leading-none tracking-tight">96%</span>
                </div>
              </div>
              <span className="text-ink-600 font-medium mt-4 text-center text-sm uppercase tracking-wider">De Afinidade</span>
            </div>

            <div className="flex-1">
              <h2 className="text-2xl sm:text-3xl font-bold text-ink-900 mb-2">{bestMatch.name}</h2>
              <p className="text-ink-600 text-[17px] mb-4">{bestMatch.desc}</p>

              <div className="flex flex-wrap gap-2 mb-6">
                <span className="bg-red-100 text-red-900 px-3 py-1 rounded-full text-sm font-semibold">{bestMatch.mainArea}</span>
                <span className="bg-white border border-line-200 text-ink-600 px-3 py-1 rounded-full text-sm font-semibold flex items-center gap-1">
                  <BookOpen size={14} /> {bestMatch.hours}
                </span>
              </div>

              <div className="bg-white rounded-lg p-4 border border-line-200">
                <h3 className="font-bold text-ink-900 mb-3">Por que este curso?</h3>
                <div className="flex flex-col gap-3">
                  {Object.entries(bestMatch.areas).map(([area, pct]) => (
                    <div key={area}>
                      <div className="flex justify-between text-sm font-semibold mb-1">
                        <span className="text-ink-900">{area}</span>
                        <span className="text-red-700">{pct}%</span>
                      </div>
                      <div className="h-2 w-full bg-red-100 rounded-full overflow-hidden">
                        <div className="h-full bg-red-600 rounded-full" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-6">
                <ButtonPrimary onClick={() => onViewCourse(bestMatch.id)}>Ver detalhes do curso</ButtonPrimary>
              </div>
            </div>
          </div>
        </div>

        <h2 className="text-xl font-bold text-ink-900 mb-4">Também combinam com você</h2>

        <div className="flex flex-col gap-4 mb-8">
          {others.map((course, idx) => (
            <div key={course.id} className="bg-white rounded-[12px] border border-line-200 p-4 sm:p-5 flex flex-col sm:flex-row gap-4 sm:items-center hover:border-red-300 transition-colors">
              <div className="flex items-center gap-4 flex-1">
                <div className="w-8 h-8 rounded-full bg-red-100 text-red-900 font-bold flex items-center justify-center shrink-0">
                  {idx + 2}
                </div>
                <div>
                  <h3 className="font-bold text-ink-900 text-lg leading-tight">{course.name}</h3>
                  <p className="text-ink-600 text-sm line-clamp-1 mt-1">{course.desc}</p>
                </div>
              </div>

              <div className="flex items-center justify-between sm:justify-end gap-6 border-t sm:border-t-0 pt-4 sm:pt-0 border-line-200 mt-2 sm:mt-0">
                <div className="flex flex-wrap gap-2">
                  <span className="bg-red-100 text-red-900 px-2 py-1 rounded text-xs font-semibold">{course.mainArea}</span>
                </div>
                <div className="flex flex-col items-end shrink-0 w-[80px]">
                  <span className="font-bold text-ink-900 tabular-nums">{90 - idx * 5}%</span>
                  <div className="h-1.5 w-full bg-line-200 rounded-full mt-1 overflow-hidden">
                    <div className="h-full bg-ink-900 rounded-full transition-all duration-1000 ease-out" style={{ width: `${90 - idx * 5}%` }} />
                  </div>
                </div>
                <button
                  onClick={() => onViewCourse(course.id)}
                  className="min-w-[48px] min-h-[48px] flex items-center justify-center text-red-600 hover:bg-red-50 rounded"
                  aria-label="Ver curso"
                >
                  <ArrowRight size={24} />
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row gap-4 pb-12">
          <ButtonSecondary onClick={() => setShowResetModal(true)}>
            <RefreshCw size={18} className="mr-2" /> Refazer o teste
          </ButtonSecondary>
          <ButtonGhost>
            <Download size={20} className="mr-2" /> Salvar resultado em PDF
          </ButtonGhost>
        </div>
      </main>

      {showResetModal && (
        <ConfirmResetModal
          onConfirm={() => { setShowResetModal(false); onReset(); }}
          onCancel={() => setShowResetModal(false)}
        />
      )}
    </div>
  );
}

function CourseDetailScreen({
  courseId,
  onBack,
  onExpressInterest,
}: {
  courseId: number;
  onBack: () => void;
  onExpressInterest: (id: number) => void;
}) {
  const course = COURSES.find(c => c.id === courseId) || COURSES[0];

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <header className="bg-ink-900 text-white p-4">
        <div className="max-w-[800px] mx-auto flex items-center">
          <button
            onClick={onBack}
            className="flex items-center font-semibold min-h-[48px] px-2 hover:bg-red-600 rounded mr-4"
          >
            <ChevronLeft size={20} className="mr-1" /> Voltar
          </button>
        </div>
      </header>

      <main className="flex-1 max-w-[800px] w-full mx-auto p-5 sm:p-8 flex flex-col">
        <div className="bg-white rounded-[12px] border border-line-200 overflow-hidden mb-8 shadow-sm">
          <div className="p-6 sm:p-8 border-b border-line-200 bg-ink-900 text-white">
            <div className="flex flex-wrap gap-2 mb-4">
              <span className="bg-red-700 text-red-100 px-3 py-1 rounded-full text-sm font-semibold">{course.mainArea}</span>
              <span className="bg-white/10 text-white border border-white/20 px-3 py-1 rounded-full text-sm font-semibold">{course.hours}</span>
            </div>
            <h1 className="text-3xl font-bold mb-4">{course.name}</h1>
            <p className="text-red-100 text-[17px] leading-relaxed max-w-[600px]">
              {course.desc} O profissional formado poderá atuar em indústrias, oficinas e concessionárias.
            </p>
          </div>

          <div className="p-6 sm:p-8">
            <h2 className="text-xl font-bold text-ink-900 mb-4">O que você vai aprender</h2>
            <ul className="list-disc pl-5 text-ink-600 space-y-2 mb-8 text-[17px]">
              <li>Fundamentos técnicos da área</li>
              <li>Práticas de laboratório e oficina</li>
              <li>Leitura e interpretação de manuais</li>
              <li>Normas de segurança e meio ambiente</li>
            </ul>

            <div className="bg-red-50 rounded-lg p-5 border border-red-100 flex items-center justify-between mb-8">
              <div>
                <h3 className="font-bold text-red-900 mb-1">Sua afinidade</h3>
                <p className="text-red-700 text-sm">Baseado nas suas respostas</p>
              </div>
              <div className="text-3xl font-bold text-red-700">85%</div>
            </div>

            <ButtonPrimary onClick={() => onExpressInterest(course.id)}>
              Manifestar interesse neste curso
            </ButtonPrimary>
          </div>
        </div>

        <div className="bg-white rounded-[12px] border border-line-200 p-6 sm:p-8 mb-12 shadow-sm">
          <h2 className="text-xl font-bold text-ink-900 mb-4">Falar com a secretaria da escola</h2>
          <p className="text-ink-600 mb-6">As matrículas estão abertas. Entre em contato para saber sobre turmas e horários.</p>

          <div className="flex flex-col sm:flex-row gap-6">
            <div className="flex items-start gap-3 flex-1">
              <MapPin className="text-red-600 shrink-0 mt-1" />
              <div>
                <h4 className="font-bold text-ink-900">Endereço</h4>
                <p className="text-ink-600 text-sm mt-1">Rua da Escola Técnica, 1000<br />Centro - Cidade</p>
              </div>
            </div>
            <div className="flex items-start gap-3 flex-1">
              <Phone className="text-red-600 shrink-0 mt-1" />
              <div>
                <h4 className="font-bold text-ink-900">Telefone / WhatsApp</h4>
                <p className="text-ink-600 text-sm mt-1">(11) 99999-0000</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function SignupModal({ onClose, onRegister }: { onClose: () => void; onRegister: () => void }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim() || !email.trim() || !password || !confirmPassword) {
      setError('Preencha todos os campos para criar sua conta.');
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setError('Informe um e-mail válido.');
      return;
    }
    if (password.length < 6) {
      setError('A senha deve ter pelo menos 6 caracteres.');
      return;
    }
    if (password !== confirmPassword) {
      setError('As senhas não coincidem.');
      return;
    }
    onRegister();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/55 p-0 sm:p-5 backdrop-blur-sm"
      role="presentation"
      onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="signup-title"
        className="w-full max-w-[520px] max-h-[92vh] overflow-y-auto rounded-t-2xl sm:rounded-2xl bg-white shadow-2xl animate-in slide-in-from-bottom-5 sm:zoom-in-95 duration-200"
      >
        <div className="flex items-start justify-between gap-5 border-b border-line-200 p-5 sm:p-7">
          <div>
            <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-red-100 text-red-600">
              <UserPlus size={21} aria-hidden="true" />
            </div>
            <h2 id="signup-title" className="text-2xl font-bold leading-tight text-ink-900">Crie sua conta</h2>
            <p className="mt-1 text-sm text-ink-600">Salve seus cursos de interesse e acesse sua lista quando quiser.</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-ink-600 transition-colors hover:bg-red-50 hover:text-red-700"
            aria-label="Fechar cadastro"
          >
            <X size={22} aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 sm:p-7">
          {error && (
            <div role="alert" className="mb-5 flex items-start gap-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-900">
              <AlertCircle size={19} className="mt-0.5 shrink-0" aria-hidden="true" />
              <span className="font-semibold">{error}</span>
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label htmlFor="signup-name" className="mb-2 block font-semibold text-ink-900">Nome completo</label>
              <input id="signup-name" autoFocus type="text" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} className="w-full min-h-[48px] rounded-[8px] border-2 border-line-200 p-3 text-[17px] text-ink-900 outline-none focus:border-red-600 focus:ring-0" />
            </div>
            <div>
              <label htmlFor="signup-email" className="mb-2 block font-semibold text-ink-900">E-mail</label>
              <input id="signup-email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full min-h-[48px] rounded-[8px] border-2 border-line-200 p-3 text-[17px] text-ink-900 outline-none focus:border-red-600 focus:ring-0" />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="signup-password" className="mb-2 block font-semibold text-ink-900">Senha</label>
                <input id="signup-password" type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full min-h-[48px] rounded-[8px] border-2 border-line-200 p-3 text-[17px] text-ink-900 outline-none focus:border-red-600 focus:ring-0" />
              </div>
              <div>
                <label htmlFor="signup-confirm-password" className="mb-2 block font-semibold text-ink-900">Confirmar senha</label>
                <input id="signup-confirm-password" type="password" autoComplete="new-password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="w-full min-h-[48px] rounded-[8px] border-2 border-line-200 p-3 text-[17px] text-ink-900 outline-none focus:border-red-600 focus:ring-0" />
              </div>
            </div>
          </div>
          <p className="mt-5 text-sm leading-relaxed text-ink-600">Ao criar sua conta, você poderá manter sua lista de interesses neste dispositivo.</p>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row-reverse">
            <ButtonPrimary type="submit" className="sm:flex-1">Criar conta</ButtonPrimary>
            <ButtonGhost className="sm:flex-1" onClick={onClose}>Cancelar</ButtonGhost>
          </div>
        </form>
      </section>
    </div>
  );
}

function LoginScreen({
  onLogin,
  onAdminLogin,
  onBack,
}: {
  onLogin: () => void;
  onAdminLogin: () => void;
  onBack: () => void;
}) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showSignupModal, setShowSignupModal] = useState(false);

  const handleLogin = () => {
    if (!email.trim() || !password) {
      setError('Preencha e-mail e senha para continuar.');
      return;
    }
    if (email.trim() === ADMIN_EMAIL && password === ADMIN_PASSWORD) {
      onAdminLogin();
      return;
    }
    setError('');
    onLogin();
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <header className="bg-ink-900 text-white p-4">
        <div className="max-w-[1440px] mx-auto flex items-center">
          <button
            onClick={onBack}
            className="flex items-center font-semibold min-h-[48px] px-2 hover:bg-red-600 rounded mr-4"
          >
            <ChevronLeft size={20} className="mr-1" /> Voltar
          </button>
        </div>
      </header>

      <main className="flex-1 max-w-[1440px] w-full mx-auto p-5 sm:p-8 flex flex-col items-center justify-center">
        <div className="max-w-[400px] w-full bg-white rounded-[12px] p-6 sm:p-10 shadow-[0_8px_24px_rgba(16,24,40,0.08)]">
          <h1 className="text-2xl font-bold text-red-900 mb-2">Entre na sua conta</h1>
          <p className="text-ink-600 mb-6">Para salvar seu interesse, precisamos saber quem é você.</p>

          {error && (
            <div role="alert" className="mb-5 flex items-start gap-3 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-900">
              <AlertCircle size={19} className="mt-0.5 shrink-0" />
              <span className="font-semibold">{error}</span>
            </div>
          )}

          <div className="mb-4">
            <label className="block font-semibold text-ink-900 mb-2">E-mail</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full border-2 border-line-200 rounded-[8px] p-3 min-h-[48px] text-[17px] focus:border-red-600 focus:ring-0 outline-none"
            />
          </div>

          <div className="mb-8">
            <label className="block font-semibold text-ink-900 mb-2">Senha</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleLogin()}
              className="w-full border-2 border-line-200 rounded-[8px] p-3 min-h-[48px] text-[17px] focus:border-red-600 focus:ring-0 outline-none"
            />
          </div>

          <div className="flex flex-col gap-3">
            <ButtonPrimary onClick={handleLogin}>Entrar</ButtonPrimary>
            <ButtonGhost onClick={() => setShowSignupModal(true)}>Cadastrar-se</ButtonGhost>
          </div>
        </div>
      </main>

      {showSignupModal && (
        <SignupModal
          onClose={() => setShowSignupModal(false)}
          onRegister={onLogin}
        />
      )}
    </div>
  );
}

function InterestListScreen({
  courseIds,
  onBack,
  showToast,
  onRemoveCourse,
  onViewCourse,
}: {
  courseIds: number[];
  onBack: () => void;
  showToast: boolean;
  onRemoveCourse: (id: number) => void;
  onViewCourse: (id: number) => void;
}) {
  const interestedCourses = COURSES.filter(c => courseIds.includes(c.id));

  return (
    <div className="min-h-screen bg-white flex flex-col relative">
      <Header hideNav />
      <main className="flex-1 max-w-[800px] w-full mx-auto p-5 sm:p-8 flex flex-col">
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={onBack}
            className="flex items-center font-semibold min-h-[48px] px-2 hover:bg-red-100 rounded text-red-700"
          >
            <ChevronLeft size={20} className="mr-1" /> Voltar
          </button>
          <h1 className="text-2xl font-bold text-red-900">Minha Lista de Interesse</h1>
        </div>

        {interestedCourses.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-16 h-16 rounded-full bg-ink-100 flex items-center justify-center mb-4">
              <List size={28} className="text-ink-400" />
            </div>
            <p className="text-ink-600 font-semibold text-lg mb-1">Sua lista está vazia</p>
            <p className="text-ink-400 text-sm">Explore os cursos e manifeste interesse para adicioná-los aqui.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {interestedCourses.map((course) => (
              <div
                key={course.id}
                className="bg-white rounded-[12px] border border-line-200 p-4 sm:p-5 flex flex-col gap-4 hover:border-red-200 hover:shadow-md transition-all duration-200"
              >
                <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-ink-900 text-lg leading-tight">{course.name}</h3>
                    <p className="text-ink-600 text-sm mt-1 line-clamp-2">{course.desc}</p>
                    <div className="flex flex-wrap gap-2 mt-3">
                      <span className="bg-red-100 text-red-900 px-2 py-1 rounded text-xs font-bold uppercase tracking-wide">
                        {course.mainArea}
                      </span>
                      <span className="bg-white border border-line-200 text-ink-600 px-2 py-1 rounded text-xs font-bold uppercase tracking-wide flex items-center gap-1">
                        <BookOpen size={11} /> {course.hours}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => onRemoveCourse(course.id)}
                    className="p-2 text-ink-300 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors active:scale-95 self-start shrink-0"
                    aria-label="Remover curso"
                    title="Remover da lista"
                  >
                    <Trash2 size={20} />
                  </button>
                </div>
                <div className="border-t border-line-200 pt-3">
                  <button
                    onClick={() => onViewCourse(course.id)}
                    className="flex items-center gap-2 text-red-600 font-semibold text-sm hover:text-red-800 hover:underline transition-colors min-h-[44px]"
                  >
                    <ArrowRight size={16} /> Ver detalhes do curso
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {showToast && (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 bg-ink-900 text-white px-6 py-3 rounded-[8px] shadow-lg font-semibold flex items-center gap-2 animate-in fade-in slide-in-from-bottom-4">
          <Check size={20} className="text-red-600" />
          Curso adicionado à lista!
        </div>
      )}
    </div>
  );
}

function AccountShell({ title, subtitle, onBack, children }: { title: string; subtitle: string; onBack: () => void; children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-bg-50 flex flex-col">
      <Header hideNav />
      <main className="w-full max-w-[900px] mx-auto px-5 py-8 sm:px-8 sm:py-12">
        <button onClick={onBack} className="mb-8 flex min-h-[44px] items-center gap-1 rounded-lg px-2 font-semibold text-red-700 hover:bg-red-50"><ChevronLeft size={20} /> Voltar</button>
        <div className="mb-8 border-l-4 border-red-600 pl-5">
          <h1 className="text-3xl font-bold text-ink-900">{title}</h1>
          <p className="mt-1 text-ink-600">{subtitle}</p>
        </div>
        {children}
      </main>
    </div>
  );
}

function ProfileScreen({ name, onBack }: { name: string; onBack: () => void }) {
  const [profileName, setProfileName] = useState(name || 'Meu perfil');
  const [email, setEmail] = useState('estudante@exemplo.com');
  const [saved, setSaved] = useState(false);
  return <AccountShell title="Meu perfil" subtitle="Mantenha seus dados de contato atualizados." onBack={onBack}>
    <form onSubmit={(e) => { e.preventDefault(); setSaved(true); }} className="max-w-[620px] rounded-2xl border border-line-200 bg-white p-6 shadow-sm sm:p-8">
      <div className="mb-7 flex items-center gap-4"><div className="grid h-16 w-16 place-items-center rounded-full bg-ink-900 text-xl font-bold text-white">{profileName.charAt(0).toUpperCase()}</div><div><p className="font-bold text-ink-900">Dados da sua conta</p><p className="text-sm text-ink-500">Usados apenas nesta experiência.</p></div></div>
      <div className="space-y-5"><label className="block font-semibold text-ink-900">Nome<input value={profileName} onChange={(e) => { setProfileName(e.target.value); setSaved(false); }} className="mt-2 w-full rounded-lg border-2 border-line-200 p-3 outline-none focus:border-red-600" /></label><label className="block font-semibold text-ink-900">E-mail<input type="email" value={email} onChange={(e) => { setEmail(e.target.value); setSaved(false); }} className="mt-2 w-full rounded-lg border-2 border-line-200 p-3 outline-none focus:border-red-600" /></label></div>
      <div className="mt-7 flex items-center gap-4"><ButtonPrimary type="submit" className="sm:w-auto">Salvar alterações</ButtonPrimary>{saved && <span role="status" className="flex items-center gap-1 text-sm font-semibold text-success"><CheckCircle size={17} /> Salvo</span>}</div>
    </form>
  </AccountShell>;
}

function TestHistoryScreen({ tests, onBack, onRestart }: { tests: TestRecord[]; onBack: () => void; onRestart: () => void }) {
  const latestTest = tests[tests.length - 1];
  const hasTest = Boolean(latestTest);
  return <AccountShell title="Meus testes" subtitle="Acompanhe o resultado mais recente do seu perfil." onBack={onBack}>
    {hasTest ? <div className="max-w-[720px] overflow-hidden rounded-2xl border border-line-200 bg-white shadow-sm"><div className="bg-ink-900 p-6 text-white"><p className="mb-2 text-xs font-bold uppercase tracking-[.16em] text-red-100">Último teste · {tests.length} realizado{tests.length > 1 ? 's' : ''}</p><h2 className="text-2xl font-bold">Perfil técnico explorador</h2><p className="mt-2 text-white/70">{new Date(latestTest.completedAt).toLocaleDateString('pt-BR')} · {latestTest.answers.length} respostas registradas</p></div><div className="grid gap-5 p-6 sm:grid-cols-[1fr_auto] sm:items-center"><div><p className="font-bold text-ink-900">Principal recomendação</p><p className="mt-1 text-lg text-red-900">Fundamentos de Inteligência Artificial</p></div><div className="flex items-center gap-3"><span className="text-3xl font-bold text-ink-900">96%</span><span className="text-sm text-ink-500">afinidade</span></div><ButtonSecondary onClick={onRestart} className="sm:col-span-2">Refazer o teste</ButtonSecondary></div></div> : <div className="max-w-[600px] rounded-2xl border border-line-200 bg-white p-10 text-center shadow-sm"><History className="mx-auto mb-4 text-red-600" size={36} /><h2 className="text-xl font-bold text-ink-900">Ainda não há testes por aqui</h2><p className="mt-2 text-ink-600">Quando você concluir o quiz, o resultado mais recente aparecerá neste espaço.</p><ButtonPrimary onClick={onRestart} className="mx-auto mt-6 sm:w-auto">Fazer meu primeiro teste</ButtonPrimary></div>}
  </AccountShell>;
}

// --- ADMIN COMPONENTS ---

function SurveyLinkModal({
  token,
  onClose,
  onPreviewSurvey,
}: {
  token: string;
  onClose: () => void;
  onPreviewSurvey: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const link = `${window.location.origin}${window.location.pathname}?survey=${token}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(link).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/55 backdrop-blur-sm"
      onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 sm:p-8 animate-in zoom-in-95 duration-200">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-full bg-ink-900 flex items-center justify-center shrink-0">
              <Link2 size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-ink-900">Link da pesquisa gerado</h2>
              <p className="text-ink-600 text-sm mt-0.5">Compartilhe com os estudantes</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center rounded-lg text-ink-400 hover:bg-red-50 hover:text-red-700 transition-colors"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="bg-ink-50 border border-line-200 rounded-xl p-4 mb-4">
          <p className="text-xs font-semibold text-ink-500 uppercase tracking-wider mb-2">Link para compartilhar</p>
          <p className="text-sm font-mono text-ink-900 break-all leading-relaxed">{link}</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 mb-5">
          <button
            onClick={handleCopy}
            className={`flex items-center justify-center gap-2 font-bold rounded-xl min-h-[48px] px-6 flex-1 transition-all duration-200 border-2 ${
              copied
                ? 'bg-green-50 border-green-500 text-green-700'
                : 'bg-white border-ink-900 text-ink-900 hover:bg-ink-50'
            }`}
          >
            {copied ? <CheckCircle size={18} /> : <Copy size={18} />}
            {copied ? 'Copiado!' : 'Copiar link'}
          </button>
          <button
            onClick={onPreviewSurvey}
            className="flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl min-h-[48px] px-6 flex-1 transition-all duration-200"
          >
            <ExternalLink size={18} /> Visualizar pesquisa
          </button>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2">
          <AlertCircle size={16} className="text-amber-600 mt-0.5 shrink-0" />
          <p className="text-amber-800 text-xs font-medium">
            O link é anônimo — nenhuma informação pessoal do estudante é coletada ou associada às respostas.
          </p>
        </div>
      </div>
    </div>
  );
}

function AdminDashboard({
  interestCounts,
  surveyResponses,
  surveyToken,
  onGenerateLink,
  onLogout,
  onPreviewSurvey,
  onViewInterests,
  onViewProfile,
  onViewTests,
}: {
  interestCounts: Record<number, number>;
  surveyResponses: SurveyResponse[];
  surveyToken: string | null;
  onGenerateLink: () => void;
  onLogout: () => void;
  onPreviewSurvey: () => void;
  onViewInterests: () => void;
  onViewProfile: () => void;
  onViewTests: () => void;
}) {
  const [showLinkModal, setShowLinkModal] = useState(false);

  const totalInterests = Object.values(interestCounts).reduce((a, b) => a + b, 0);
  const totalSurveyResponses = surveyResponses.length;
  const coursesWithInterest = Object.values(interestCounts).filter(v => v > 0).length;

  const sortedCourses = [...COURSES].sort(
    (a, b) => (interestCounts[b.id] ?? 0) - (interestCounts[a.id] ?? 0)
  );
  const mostWanted = sortedCourses.slice(0, 3);
  const leastWanted = sortedCourses.slice(-3).reverse();
  const courseChartData = [...mostWanted, ...leastWanted].map((course) => ({
    name: course.name.replace('Fundamentos de ', '').replace('Manutenção ', ''),
    interests: interestCounts[course.id] ?? 0,
    group: mostWanted.some((item) => item.id === course.id) ? 'top' : 'bottom',
  }));
  const maxCount = Math.max(...Object.values(interestCounts), 1);

  const handleGenerateLink = () => {
    onGenerateLink();
    setShowLinkModal(true);
  };

  const handleShowExistingLink = () => {
    setShowLinkModal(true);
  };

  // Aggregate survey results per question
  const surveyAggregated = SURVEY_QUESTIONS.map((q, qIdx) => {
    const counts = q.options.map((_, oIdx) =>
      surveyResponses.filter(r => r.answers[qIdx] === oIdx).length
    );
    const total = counts.reduce((a, b) => a + b, 0) || 1;
    return { question: q, counts, total };
  });
  const surveyHighlights = surveyAggregated.map(({ question, counts, total }) => {
    const answerIndex = counts.indexOf(Math.max(...counts));
    return { label: question.options[answerIndex], count: counts[answerIndex], total };
  }).sort((a, b) => b.count - a.count).slice(0, 3);
  const surveyPieData = surveyHighlights.map((item) => ({ name: item.label, value: item.count }));

  const areaColors: Record<string, string> = {
    'Mecânica Automotiva': 'bg-orange-100 text-orange-800',
    'Elétrica': 'bg-yellow-100 text-yellow-800',
    'Eletromecânica': 'bg-blue-100 text-blue-800',
    'Inteligência Artificial': 'bg-purple-100 text-purple-800',
    'Tecnologia da Informação': 'bg-cyan-100 text-cyan-800',
    'Costura': 'bg-pink-100 text-pink-800',
    'Mecânica': 'bg-stone-100 text-stone-800',
  };

  return (
    <div className="min-h-screen bg-[#f5f5f5] flex flex-col">
      <Header isLoggedIn isAdmin onViewInterests={onViewInterests} onViewProfile={onViewProfile} onViewTests={onViewTests} onViewDashboard={() => undefined} onLogout={onLogout} />

      <main className="flex-1 max-w-[1280px] w-full mx-auto px-4 sm:px-6 py-8">

        {/* Page Title + Generate Link Button */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-ink-900">Dashboard</h1>
            <p className="text-ink-500 text-sm mt-1">Visão agregada de interesses e respostas de pesquisa</p>
          </div>
          <div className="flex gap-3">
            {surveyToken ? (
              <button
                onClick={handleShowExistingLink}
                className="flex items-center gap-2 bg-white border-2 border-ink-900 text-ink-900 hover:bg-ink-50 font-bold rounded-xl px-5 min-h-[48px] transition-all duration-200 text-sm shadow-sm"
              >
                <Link2 size={16} /> Ver link ativo
              </button>
            ) : null}
            <button
              onClick={handleGenerateLink}
              className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded-xl px-5 min-h-[48px] transition-all duration-200 text-sm shadow-sm active:scale-95"
            >
              <ClipboardList size={16} /> {surveyToken ? 'Novo link de pesquisa' : 'Gerar link de pesquisa'}
            </button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {[
            { label: 'Total de manifestações', value: totalInterests, icon: TrendingUp, note: 'em todos os cursos' },
            { label: 'Respostas da pesquisa', value: totalSurveyResponses, icon: ClipboardList, note: 'anônimas' },
            { label: 'Cursos com interesse', value: coursesWithInterest, icon: Users, note: `de ${COURSES.length} cursos` },
          ].map((stat) => (
            <div key={stat.label} className="bg-white rounded-2xl border border-line-200 p-5 flex items-start gap-4 shadow-sm">
              <div className="w-11 h-11 rounded-xl bg-ink-900 flex items-center justify-center shrink-0">
                <stat.icon size={20} className="text-white" />
              </div>
              <div>
                <p className="text-ink-500 text-sm font-medium">{stat.label}</p>
                <p className="text-3xl font-bold text-ink-900 leading-none mt-1">{stat.value}</p>
                <p className="text-ink-400 text-xs mt-1">{stat.note}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mb-8 grid gap-5 lg:grid-cols-[1.45fr_.85fr]">
          <section className="rounded-2xl border border-line-200 bg-white p-5 shadow-sm sm:p-6">
            <div className="mb-4 flex items-center gap-2"><BarChart3 size={20} className="text-red-600" /><h2 className="font-bold text-ink-900">Pulso de interesse</h2></div>
            <div className="h-[230px]" aria-label="Gráfico comparativo de manifestações de interesse">
              <ResponsiveContainer width="100%" height="100%"><BarChart data={courseChartData} margin={{ top: 8, right: 4, left: -20, bottom: 8 }}><XAxis dataKey="name" tick={{ fontSize: 11, fill: '#52525B' }} interval={0} tickLine={false} axisLine={false} /><YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#71717A' }} tickLine={false} axisLine={false} /><Tooltip cursor={{ fill: '#FEF5F4' }} contentStyle={{ borderRadius: 10, border: '1px solid #E4E4E7' }} /><Bar dataKey="interests" radius={[5, 5, 0, 0]}>{courseChartData.map((entry, index) => <Cell key={index} fill={entry.group === 'top' ? '#D9251C' : '#A1A1AA'} />)}</Bar></BarChart></ResponsiveContainer>
            </div>
            <div className="mt-1 flex gap-5 text-xs font-semibold text-ink-500"><span className="flex items-center gap-2"><i className="h-2 w-2 rounded-full bg-red-600" /> 3 maiores</span><span className="flex items-center gap-2"><i className="h-2 w-2 rounded-full bg-ink-400" /> 3 menores</span></div>
          </section>
          <section className="rounded-2xl border border-line-200 bg-ink-900 p-5 text-white shadow-sm sm:p-6">
            <p className="text-xs font-bold uppercase tracking-[.14em] text-red-100">Pesquisa anônima</p><h2 className="mt-2 font-bold">Sinais mais frequentes</h2>
            <div className="mt-2 h-[174px]"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={surveyPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={42} outerRadius={70} paddingAngle={3}>{surveyPieData.map((_, index) => <Cell key={index} fill={['#D9251C', '#F0908C', '#FFFFFF'][index]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></div>
            <p className="text-center text-xs text-white/65">Respostas agregadas, sem identificação.</p>
          </section>
        </div>

        {/* Course Interest Table */}
        <div className="bg-white rounded-2xl border border-line-200 shadow-sm mb-8 overflow-hidden">
          <div className="p-5 sm:p-6 border-b border-line-200 flex items-center gap-3">
            <BarChart2 size={20} className="text-red-600" />
            <div><h2 className="text-lg font-bold text-ink-900">Ranking de interesse</h2><p className="mt-0.5 text-sm text-ink-500">Os 3 cursos mais procurados e os 3 com menor procura.</p></div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line-200 bg-[#fafafa]">
                  <th className="text-left px-5 sm:px-6 py-3 text-xs font-bold text-ink-500 uppercase tracking-wider w-8">#</th>
                  <th className="text-left px-3 py-3 text-xs font-bold text-ink-500 uppercase tracking-wider">Curso</th>
                  <th className="text-left px-3 py-3 text-xs font-bold text-ink-500 uppercase tracking-wider hidden sm:table-cell">Área</th>
                  <th className="text-right px-5 sm:px-6 py-3 text-xs font-bold text-ink-500 uppercase tracking-wider">Interesses</th>
                </tr>
              </thead>
              <tbody>
                {[...mostWanted, ...leastWanted].map((course, idx) => {
                  const count = interestCounts[course.id] ?? 0;
                  const barWidth = maxCount > 0 ? Math.round((count / maxCount) * 100) : 0;
                  const isTop = idx < 3;
                  return (
                    <tr key={course.id} className="border-b border-line-200 last:border-0 hover:bg-[#fafafa] transition-colors">
                      <td className="px-5 sm:px-6 py-4 text-ink-400 font-mono text-xs tabular-nums">{isTop ? `TOP ${idx + 1}` : `BAIXO ${idx - 2}`}</td>
                      <td className="px-3 py-4">
                        <div>
                          <p className="font-semibold text-ink-900 leading-tight">{course.name}</p>
                          <div className="mt-2 flex items-center gap-2">
                            <div className="flex-1 max-w-[180px] h-1.5 bg-line-200 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all duration-700 ${isTop ? 'bg-red-600' : 'bg-ink-400'}`}
                                style={{ width: `${barWidth}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-4 hidden sm:table-cell">
                        <span className={`text-xs font-bold px-2 py-1 rounded ${areaColors[course.mainArea] ?? 'bg-gray-100 text-gray-700'}`}>
                          {course.mainArea}
                        </span>
                      </td>
                      <td className="px-5 sm:px-6 py-4 text-right">
                        <span className="font-bold text-xl text-ink-900 tabular-nums">{count}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Survey Results */}
        <div className="bg-white rounded-2xl border border-line-200 shadow-sm overflow-hidden">
          <div className="p-5 sm:p-6 border-b border-line-200 flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <ClipboardList size={20} className="text-red-600" />
              <h2 className="text-lg font-bold text-ink-900">Resultados da pesquisa</h2>
            </div>
            <span className="text-sm font-semibold text-ink-500 bg-[#f5f5f5] px-3 py-1 rounded-full">
              {totalSurveyResponses} resposta{totalSurveyResponses !== 1 ? 's' : ''}
            </span>
          </div>

          {totalSurveyResponses === 0 ? (
            <div className="p-12 flex flex-col items-center text-center">
              <div className="w-14 h-14 rounded-full bg-ink-100 flex items-center justify-center mb-4">
                <ClipboardList size={24} className="text-ink-400" />
              </div>
              <p className="font-semibold text-ink-600">Nenhuma resposta ainda</p>
              <p className="text-ink-400 text-sm mt-1">Gere e compartilhe o link da pesquisa para começar a coletar dados.</p>
            </div>
          ) : (
            <div className="grid gap-4 p-5 sm:grid-cols-3 sm:p-6">
              {surveyHighlights.map((item, idx) => {
                const percentage = Math.round((item.count / item.total) * 100);
                return <div key={item.label} className="rounded-xl border border-line-200 bg-[#fafafa] p-4">
                  <p className="text-xs font-bold uppercase tracking-wider text-ink-500">Insight {idx + 1}</p>
                  <p className="mt-3 min-h-[48px] font-bold leading-snug text-ink-900">{item.label}</p>
                  <div className="mt-4 flex items-end justify-between"><span className="text-3xl font-bold text-red-700">{percentage}%</span><span className="text-xs font-semibold text-ink-500">{item.count} respostas</span></div>
                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-line-200"><div className="h-full rounded-full bg-red-600" style={{ width: `${percentage}%` }} /></div>
                </div>;
              })}
            </div>
          )}
        </div>

        <p className="text-center text-ink-400 text-xs mt-6">
          Nenhuma informação pessoal é exibida. Todos os dados são agregados e anônimos.
        </p>
      </main>

      {showLinkModal && surveyToken && (
        <SurveyLinkModal
          token={surveyToken}
          onClose={() => setShowLinkModal(false)}
          onPreviewSurvey={() => { setShowLinkModal(false); onPreviewSurvey(); }}
        />
      )}
    </div>
  );
}

// --- SURVEY SCREEN ---

function SurveyScreen({ onSubmit }: { onSubmit: (answers: number[]) => void }) {
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [error, setError] = useState(false);

  const q = SURVEY_QUESTIONS[currentQ];
  const selected = answers[currentQ];

  const handleNext = () => {
    if (selected === undefined) {
      setError(true);
      return;
    }
    setError(false);
    if (currentQ < SURVEY_QUESTIONS.length - 1) {
      setCurrentQ(currentQ + 1);
    } else {
      onSubmit(answers);
    }
  };

  const handlePrev = () => {
    if (currentQ > 0) setCurrentQ(currentQ - 1);
  };

  const isLast = currentQ === SURVEY_QUESTIONS.length - 1;

  return (
    <div className="min-h-screen bg-white flex flex-col pb-24">
      <header className="bg-ink-900 text-white">
        <div className="max-w-[1440px] mx-auto px-4 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-red-600 flex items-center justify-center shrink-0">
            <ClipboardList size={16} className="text-white" />
          </div>
          <div>
            <p className="font-bold leading-none">Pesquisa de Interesse</p>
            <p className="text-white/60 text-xs mt-0.5">QuizPessoal · SENAI</p>
          </div>
        </div>
        <div className="h-1.5 w-full bg-white/10">
          <div
            className="h-full bg-red-500 transition-all duration-300"
            style={{ width: `${((currentQ + 1) / SURVEY_QUESTIONS.length) * 100}%` }}
          />
        </div>
      </header>

      <main className="flex-1 max-w-[600px] w-full mx-auto p-5 sm:p-8 flex flex-col">
        <div className="mb-6">
          <p className="text-xs font-bold text-ink-400 uppercase tracking-wider mb-1">
            Pergunta {currentQ + 1} de {SURVEY_QUESTIONS.length}
          </p>
          <h2 className="text-2xl font-bold text-ink-900 leading-tight">
            <span className="text-red-600 mr-2">{currentQ + 1}.</span>
            {q.text}
          </h2>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-300 rounded-lg p-3 mb-5 flex items-center gap-2 text-sm">
            <AlertCircle size={16} className="text-red-600 shrink-0" />
            <span className="font-semibold text-red-900">Selecione uma opção para continuar.</span>
          </div>
        )}

        <div className="flex flex-col gap-3">
          {q.options.map((opt, idx) => {
            const isSelected = selected === idx;
            return (
              <button
                key={idx}
                onClick={() => {
                  setError(false);
                  const next = [...answers];
                  next[currentQ] = idx;
                  setAnswers(next);
                }}
                className={`
                  flex items-center text-left p-4 rounded-xl min-h-[64px] border-2 transition-all duration-150 group
                  ${isSelected
                    ? 'border-red-600 bg-red-50 ring-1 ring-red-600'
                    : 'border-line-200 bg-white hover:border-red-300 hover:shadow-sm'
                  }
                `}
              >
                <div className={`
                  w-7 h-7 rounded-full flex items-center justify-center shrink-0 mr-3 font-bold text-sm transition-colors
                  ${isSelected ? 'bg-red-600 text-white' : 'bg-line-200 text-ink-500 group-hover:bg-red-100 group-hover:text-red-800'}
                `}>
                  {String.fromCharCode(65 + idx)}
                </div>
                <span className={`flex-1 text-[15px] leading-snug ${isSelected ? 'font-bold text-red-900' : 'text-ink-900'}`}>
                  {opt}
                </span>
                {isSelected && <Check size={18} className="text-red-600 ml-2 shrink-0" />}
              </button>
            );
          })}
        </div>

        <p className="text-ink-400 text-xs text-center mt-8">
          Pesquisa 100% anônima. Nenhum dado pessoal é coletado.
        </p>
      </main>

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-line-200 shadow-[0_-4px_16px_rgba(0,0,0,0.05)]">
        <div className="max-w-[600px] mx-auto flex gap-3">
          {currentQ > 0 && (
            <button
              onClick={handlePrev}
              className="flex items-center gap-1 text-red-600 font-bold border-2 border-red-200 hover:bg-red-50 rounded-xl px-5 min-h-[52px] transition-all"
            >
              <ChevronLeft size={18} /> Voltar
            </button>
          )}
          <ButtonPrimary onClick={handleNext} className="flex-1">
            {isLast ? 'Enviar respostas' : 'Próxima'}
            {!isLast && <ArrowRight size={18} className="ml-2" />}
          </ButtonPrimary>
        </div>
      </div>
    </div>
  );
}

function SurveyCompleteScreen() {
  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-5">
      <div className="bg-white rounded-2xl border border-line-200 shadow-sm p-10 max-w-md w-full text-center animate-in zoom-in-95 duration-300">
        <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
          <CheckCircle size={40} className="text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-ink-900 mb-3">Obrigado pela participação!</h2>
        <p className="text-ink-600 text-[17px] mb-2">
          Suas respostas foram registradas de forma anônima e vão ajudar a melhorar a oferta de cursos.
        </p>
        <p className="text-ink-400 text-sm">
          Você pode fechar esta página.
        </p>
      </div>
    </div>
  );
}

// --- MAIN APP ---

export default function App() {
  const [screen, setScreen] = useState<Screen>('welcome');
  const [previousScreen, setPreviousScreen] = useState<Screen | null>(null);
  const [userName, setUserName] = useState('');
  const [answers, setAnswers] = useState<number[]>([]);
  const [testHistory, setTestHistory] = useState<TestRecord[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [viewingCourseId, setViewingCourseId] = useState<number | null>(null);

  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [interestedCourseIds, setInterestedCourseIds] = useState<number[]>([]);
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [pendingInterestCourseId, setPendingInterestCourseId] = useState<number | null>(null);

  // Admin state
  const [globalInterestCounts, setGlobalInterestCounts] = useState<Record<number, number>>(SEEDED_INTEREST_COUNTS);
  const [surveyResponses, setSurveyResponses] = useState<SurveyResponse[]>(SEEDED_SURVEY_RESPONSES);
  const [surveyToken, setSurveyToken] = useState<string | null>(null);

  // Check URL for survey token on load
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('survey');
    if (token) {
      setScreen('survey');
    }
  }, []);

  const navigateTo = useCallback((newScreen: Screen) => {
    if (['welcome', 'result', 'detail', 'interestList'].includes(screen)) {
      setPreviousScreen(screen);
    }
    setScreen(newScreen);
  }, [screen]);

  const startQuiz = (name: string) => {
    setUserName(name);
    setAnswers([]);
    setCurrentQuestion(0);
    navigateTo('quiz');
  };

  const handleSelectAnswer = (qIndex: number, oIndex: number) => {
    const newAnswers = [...answers];
    newAnswers[qIndex] = oIndex;
    setAnswers(newAnswers);
  };

  const nextQuestion = () => {
    if (currentQuestion < QUESTIONS.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      setTestHistory((history) => [...history, { answers: [...answers], completedAt: new Date().toISOString() }]);
      navigateTo('calculating');
      setTimeout(() => navigateTo('result'), 2000);
    }
  };

  const prevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    } else {
      navigateTo('welcome');
    }
  };

  const resetQuiz = () => {
    setAnswers([]);
    setCurrentQuestion(0);
    navigateTo('welcome');
  };

  const viewCourse = (id: number) => {
    setViewingCourseId(id);
    navigateTo('detail');
  };

  const handleExpressInterest = (id: number) => {
    if (isLoggedIn) {
      addCourseToInterest(id);
    } else {
      setPendingInterestCourseId(id);
      navigateTo('login');
    }
  };

  const handleLogin = () => {
    setIsLoggedIn(true);
    if (pendingInterestCourseId) {
      addCourseToInterest(pendingInterestCourseId);
      setPendingInterestCourseId(null);
    } else {
      setScreen(previousScreen || 'welcome');
    }
  };

  const handleAdminLogin = () => {
    setIsAdmin(true);
    setIsLoggedIn(true);
    setScreen('adminDashboard');
  };

  const handleAdminLogout = () => {
    setIsAdmin(false);
    setIsLoggedIn(false);
    setScreen('welcome');
  };

  const handleLogout = () => {
    setIsAdmin(false);
    setIsLoggedIn(false);
    setScreen('welcome');
  };

  const accountNavigation = {
    isAdmin,
    onViewProfile: () => navigateTo('profile'),
    onViewTests: () => navigateTo('testHistory'),
    onViewDashboard: () => setScreen('adminDashboard'),
    onLogout: handleLogout,
  };

  const addCourseToInterest = (courseId: number) => {
    if (!interestedCourseIds.includes(courseId)) {
      setInterestedCourseIds(prev => [...prev, courseId]);
      // Increment global count (simulating other users)
      setGlobalInterestCounts(prev => ({
        ...prev,
        [courseId]: (prev[courseId] ?? 0) + 1,
      }));
    }
    navigateTo('interestList');
    setShowSuccessToast(true);
    setTimeout(() => setShowSuccessToast(false), 2000);
  };

  const removeCourseFromInterest = (courseId: number) => {
    setInterestedCourseIds(prev => prev.filter(id => id !== courseId));
  };

  const handleGenerateLink = () => {
    setSurveyToken(generateToken());
  };

  const handleSurveySubmit = (surveyAnswers: number[]) => {
    setSurveyResponses(prev => [
      ...prev,
      { answers: surveyAnswers, submittedAt: new Date().toISOString() },
    ]);
    setScreen('surveyComplete');
  };

  return (
    <div className="font-sans text-ink-900 selection:bg-red-100 selection:text-red-900 min-h-screen flex flex-col">
      <div className="animate-in fade-in duration-500 flex-1 flex flex-col">

        {screen === 'welcome' && (
          <WelcomeScreen
            onStart={startQuiz}
            isLoggedIn={isLoggedIn}
            {...accountNavigation}
            onLoginClick={() => navigateTo('login')}
            onViewInterests={() => navigateTo('interestList')}
          />
        )}

        {screen === 'quiz' && (
          <QuizScreen
            questionIndex={currentQuestion}
            answers={answers}
            onSelect={handleSelectAnswer}
            onNext={nextQuestion}
            onPrev={prevQuestion}
          />
        )}

        {screen === 'calculating' && <CalculatingScreen />}

        {screen === 'result' && (
          <ResultScreen
            name={userName}
            onReset={resetQuiz}
            onViewCourse={viewCourse}
            isLoggedIn={isLoggedIn}
            {...accountNavigation}
            onLoginClick={() => navigateTo('login')}
            onViewInterests={() => navigateTo('interestList')}
          />
        )}

        {screen === 'detail' && viewingCourseId && (
          <CourseDetailScreen
            courseId={viewingCourseId}
            onBack={() => setScreen(previousScreen || 'result')}
            onExpressInterest={handleExpressInterest}
          />
        )}

        {screen === 'login' && (
          <LoginScreen
            onLogin={handleLogin}
            onAdminLogin={handleAdminLogin}
            onBack={() => setScreen(previousScreen || 'welcome')}
          />
        )}

        {screen === 'interestList' && (
          <InterestListScreen
            courseIds={interestedCourseIds}
            onBack={() => setScreen(previousScreen || 'welcome')}
            showToast={showSuccessToast}
            onRemoveCourse={removeCourseFromInterest}
            onViewCourse={viewCourse}
          />
        )}

        {screen === 'profile' && (
          <ProfileScreen
            name={userName}
            onBack={() => setScreen(previousScreen || 'welcome')}
          />
        )}

        {screen === 'testHistory' && (
          <TestHistoryScreen
            tests={testHistory}
            onBack={() => setScreen(previousScreen || 'welcome')}
            onRestart={() => resetQuiz()}
          />
        )}

        {screen === 'adminDashboard' && (
          <AdminDashboard
            interestCounts={globalInterestCounts}
            surveyResponses={surveyResponses}
            surveyToken={surveyToken}
            onGenerateLink={handleGenerateLink}
            onLogout={handleAdminLogout}
            onPreviewSurvey={() => setScreen('survey')}
            onViewInterests={() => navigateTo('interestList')}
            onViewProfile={() => navigateTo('profile')}
            onViewTests={() => navigateTo('testHistory')}
          />
        )}

        {screen === 'survey' && (
          <SurveyScreen onSubmit={handleSurveySubmit} />
        )}

        {screen === 'surveyComplete' && <SurveyCompleteScreen />}

      </div>
    </div>
  );
}
