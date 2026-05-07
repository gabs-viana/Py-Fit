import React from 'react';
import { createPortal } from 'react-dom';
import './DailyModal.css';

export default function DailyModal({ data, onClose }) {
  if (!data) return null;

  const handleOverlayClick = (e) => {
    if (e.target.className.includes('modal-overlay')) {
      onClose();
    }
  };

  const formatSleep = (hours) => {
    if (!hours) return "0h";
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  };

  // Readiness Index — calculado no backend, fallback no frontend
  const readiness = data.readiness;
  const hasReadiness = readiness !== null && readiness !== undefined;
  
  const getReadinessColor = (val) => {
    if (val >= 75) return 'var(--success)';
    if (val >= 50) return 'var(--warning)';
    return 'var(--danger)';
  };
  
  const getReadinessLabel = (val) => {
    if (val >= 75) return 'PRONTO';
    if (val >= 50) return 'ALERTA';
    return 'RECUPERAR';
  };

  // Sono — Fases
  const sonoRem = data.sono?.rem_min;
  const sonoProfundo = data.sono?.profundo_min;
  const sonoLeve = data.sono?.leve_min;
  const hasSonoFases = sonoRem != null || sonoProfundo != null || sonoLeve != null;
  const sonoTotal = (sonoRem || 0) + (sonoProfundo || 0) + (sonoLeve || 0);

  return createPortal(
    <div className="modal-overlay animate-fade-in" onClick={handleOverlayClick}>
      <div className="modal-content glass-card" style={{maxWidth: '720px'}}>
        <button className="modal-close" onClick={onClose}>&times;</button>
        
        {/* ===== HEADER HERO ===== */}
        <div className="modal-header" style={{flexDirection: 'column', alignItems: 'flex-start', gap: '0.8rem'}}>
          <div style={{display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center'}}>
            <h2>📅 {data.data}</h2>
            <div className="modal-score-badge">Score: {data.score}/1000</div>
          </div>
          
          {hasReadiness && (
            <div style={{
              width: '100%',
              background: 'rgba(0,0,0,0.3)',
              borderRadius: '12px',
              padding: '1.2rem 1.5rem',
              border: `1px solid ${getReadinessColor(readiness)}30`,
              display: 'flex',
              alignItems: 'center',
              gap: '1.5rem'
            }}>
              <div style={{position: 'relative', width: '70px', height: '70px', flexShrink: 0}}>
                <svg viewBox="0 0 36 36" style={{width: '100%', height: '100%', transform: 'rotate(-90deg)'}}>
                  <circle cx="18" cy="18" r="15.5" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="3"/>
                  <circle cx="18" cy="18" r="15.5" fill="none"
                    stroke={getReadinessColor(readiness)}
                    strokeWidth="3"
                    strokeDasharray={`${readiness * 0.974} 100`}
                    strokeLinecap="round"
                  />
                </svg>
                <span style={{
                  position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                  fontSize: '1.1rem', fontWeight: 800, fontFamily: "'Outfit', sans-serif",
                  color: getReadinessColor(readiness)
                }}>{Math.round(readiness)}</span>
              </div>
              <div>
                <strong style={{color: getReadinessColor(readiness), fontSize: '1.1rem', letterSpacing: '1px'}}>
                  🧬 READINESS: {getReadinessLabel(readiness)}
                </strong>
                <br/>
                <small style={{color: 'var(--text-secondary)'}}>
                  Índice de Prontidão Atlética (HRV + RHR + Sono Profundo + Estresse)
                </small>
              </div>
            </div>
          )}
        </div>

        <div className="modal-body">
          {/* ===== SEÇÃO 1: BIO-RECOVERY ===== */}
          <div className="modal-section">
            <h3>🟢 Bio-Recovery</h3>
            <div className="modal-grid">
              <div className="modal-item">
                <span className="icon">💤</span>
                <div>
                  <strong>Sono:</strong> {formatSleep(data.sono?.horas)} (Qual. {data.sono?.qualidade || 0}%)<br/>
                  <small>Bio Manhã: {data.sono?.bio_manha || 0} | Noite: {data.sono?.bio_noite || 0}</small>
                </div>
              </div>
              <div className="modal-item">
                <span className="icon">❤️</span>
                <div>
                  <strong>Sinais Vitais:</strong><br/>
                  <small>
                    RHR: <strong>{data.wearable?.rhr || '--'} bpm</strong>
                    {data.wearable?.hrv_ms != null && <> | HRV: <strong>{data.wearable.hrv_ms} ms</strong></>}
                  </small>
                </div>
              </div>
            </div>
            
            {/* Barra de Composição do Sono */}
            {hasSonoFases && sonoTotal > 0 && (
              <div style={{marginTop: '1rem'}}>
                <small style={{color: 'var(--text-secondary)', marginBottom: '0.4rem', display: 'block'}}>Arquitetura do Sono</small>
                <div style={{display: 'flex', height: '18px', borderRadius: '9px', overflow: 'hidden', background: 'rgba(255,255,255,0.03)'}}>
                  {sonoProfundo > 0 && (
                    <div style={{width: `${(sonoProfundo/sonoTotal)*100}%`, background: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                      <span style={{fontSize: '0.6rem', color: '#fff', fontWeight: 700}}>{sonoProfundo}m</span>
                    </div>
                  )}
                  {sonoRem > 0 && (
                    <div style={{width: `${(sonoRem/sonoTotal)*100}%`, background: '#8b5cf6', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                      <span style={{fontSize: '0.6rem', color: '#fff', fontWeight: 700}}>{sonoRem}m</span>
                    </div>
                  )}
                  {sonoLeve > 0 && (
                    <div style={{width: `${(sonoLeve/sonoTotal)*100}%`, background: '#a78bfa', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                      <span style={{fontSize: '0.6rem', color: '#fff', fontWeight: 700}}>{sonoLeve}m</span>
                    </div>
                  )}
                </div>
                <div style={{display: 'flex', gap: '1rem', marginTop: '0.4rem'}}>
                  <small style={{color: '#6366f1'}}>■ Profundo</small>
                  <small style={{color: '#8b5cf6'}}>■ REM</small>
                  <small style={{color: '#a78bfa'}}>■ Leve</small>
                </div>
              </div>
            )}
          </div>

          {/* ===== SEÇÃO 2: METABOLISMO & ATIVIDADE ===== */}
          <div className="modal-section">
            <h3>⚡ Metabolismo & Atividade</h3>
            <div className="modal-grid">
              <div className="modal-item">
                <span className="icon">🏃</span>
                <div>
                  <strong>Atividade Diária:</strong><br/>
                  <small>
                    {data.wearable?.passos || 0} passos | PAI: {data.wearable?.pai ?? '--'}
                    {data.wearable?.calorias_ativas != null && <> | {data.wearable.calorias_ativas} kcal</>}
                  </small>
                </div>
              </div>
              <div className="modal-item">
                <span className="icon">🧠</span>
                <div>
                  <strong>Estado & Estresse:</strong><br/>
                  <small>
                    Energia {data.estado?.energia}/10 | Foco {data.estado?.foco}/10<br/>
                    Estresse: {data.estado?.estresse || 0}%
                  </small>
                </div>
              </div>
              <div className="modal-item">
                <span className="icon">💧</span>
                <div>
                  <strong>Hábitos & Corpo:</strong><br/>
                  <small>
                    {data.habitos?.agua_litros || 0}L Água
                    {data.corpo?.peso ? ` | Peso: ${data.corpo.peso}kg` : ''}
                    {data.corpo?.cintura ? ` | Cintura: ${data.corpo.cintura}cm` : ''}
                  </small>
                </div>
              </div>
            </div>
          </div>

          {/* ===== SEÇÃO 3: PERFORMANCE ===== */}
          <div className="modal-section">
            <h3>🏋️ Treino: {data.treino?.planejado || 'Descanso'}</h3>
            {data.treino?.planejado !== 'Descanso' ? (
              <div className="treino-details">
                <p><strong>Executado:</strong> {data.treino?.executado === 's' ? 'Sim ✅' : 'Não ❌'}</p>
                {data.treino?.executado === 's' ? (
                  <>
                    <p><strong>Completude:</strong> {data.treino?.completude}% | <strong>Intensidade:</strong> {data.treino?.intensidade}/10</p>
                    {data.treino?.feeling && <p><strong>Feeling:</strong> {data.treino.feeling}</p>}
                  </>
                ) : (
                  <>
                    <p><strong>Remanejado:</strong> {data.treino?.remanejado === 's' ? 'Sim' : 'Não'}</p>
                    {data.treino?.justificativa && <p><strong>Justificativa:</strong> {data.treino.justificativa}</p>}
                  </>
                )}
              </div>
            ) : (
              <p style={{color: 'var(--text-muted)'}}>Dia de Descanso.</p>
            )}
          </div>

          {/* ===== SEÇÃO 4: NARRATIVA ===== */}
          <div className="modal-section">
            <h3>📝 Narrativa & Nutrição</h3>
            {data.contexto && (
              <p><strong>Obstáculo/Vitória do dia:</strong><br/>{data.contexto}</p>
            )}
            {data.alimentacao?.descricao && (
              <p style={{marginTop: '0.8rem'}}><strong>Alimentação:</strong><br/>{data.alimentacao.descricao}</p>
            )}
            {!data.contexto && !data.alimentacao?.descricao && (
              <p style={{color: 'var(--text-muted)'}}>Sem registros narrativos para este dia.</p>
            )}
          </div>

        </div>
      </div>
    </div>,
    document.body
  );
}
