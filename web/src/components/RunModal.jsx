import React from 'react';
import { createPortal } from 'react-dom';
import './DailyModal.css'; 

export default function RunModal({ run, onClose }) {
  if (!run) return null;

  const res = run.resumo || {};
  const v6 = run.v6_elite || {};
  const aval = run.avaliacao || {};
  const blocos = run.blocos || [];

  const handleOverlayClick = (e) => {
    if (e.target.className.includes('modal-overlay')) {
      onClose();
    }
  };

  const formatTempo = (seg) => {
    if (!seg) return '--';
    const m = Math.floor(seg / 60);
    const s = Math.floor(seg % 60);
    return `${m}m ${s}s`;
  };

  const formatNum = (num, decimals = 1) => {
    if (num === null || num === undefined) return '--';
    if (typeof num === 'number') return Number(num).toFixed(decimals);
    if (typeof num === 'string' && !isNaN(Number(num))) return Number(num).toFixed(decimals);
    return num;
  };

  const formatPace = (dist_km, tempo_s, explicitPace) => {
    if (explicitPace && explicitPace !== '--') return explicitPace;
    if (!dist_km || !tempo_s || dist_km <= 0) return '--';
    const pace_min = (tempo_s / 60) / dist_km;
    const m = Math.floor(pace_min);
    const s = Math.floor((pace_min - m) * 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return createPortal(
    <div className="modal-overlay animate-fade-in" onClick={handleOverlayClick}>
      <div className="modal-content glass-card" style={{maxWidth: '800px'}}>
        <button className="modal-close" onClick={onClose}>&times;</button>
        
        <div className="modal-header" style={{flexDirection: 'column', alignItems: 'flex-start', gap: '1rem'}}>
          <div>
            <h2 style={{color: 'var(--accent-secondary)'}}>{aval.tipo_treino_detectado?.toUpperCase() || 'TREINO'}</h2>
            <p style={{color: 'var(--text-muted)'}}>{formatNum(res.dist_km, 2)} km em {formatTempo(res.tempo_s)}</p>
          </div>
          <div className="modal-score-badge" style={{alignSelf: 'flex-start'}}>
            Score Fisiológico do Treino: {aval.score_0_10}/10
          </div>
        </div>

        <div className="modal-body">
          {/* V6 ELITE ALERTS */}
          <div className="modal-section" style={{background: 'rgba(139, 92, 246, 0.05)', padding: '1.5rem', borderRadius: '8px', border: '1px solid rgba(139, 92, 246, 0.2)'}}>
            <h3 style={{color: 'var(--accent-secondary)'}}>Análise Fisiológica V6 (Elite)</h3>
            <div className="modal-grid">
              <div className="modal-item">
                <span className="icon">🧠</span>
                <div>
                  <strong>Estado Autonômico:</strong><br/>
                  <small style={{color: v6.dominancia_simpatica?.includes('vermelho') ? 'var(--danger)' : (v6.dominancia_simpatica?.includes('verde') ? 'var(--success)' : 'var(--warning)'), fontWeight: 'bold'}}>
                    {v6.dominancia_simpatica?.toUpperCase()}
                  </small>
                </div>
              </div>
              <div className="modal-item">
                <span className="icon">🔥</span>
                <div>
                  <strong>Fluxo Metabólico Útil:</strong><br/>
                  <small>{v6.tempo_fluxo_util_min} minutos contínuos</small>
                </div>
              </div>
              {v6.pacing_emocional_detectado && (
                <div className="modal-item" style={{borderColor: 'var(--warning)'}}>
                  <span className="icon">⚠️</span>
                  <div>
                    <strong style={{color: 'var(--warning)'}}>Falha de Pacing Detectada</strong><br/>
                    <small>Aceleração excessiva/emocional nos primeiros 15% do treino identificada pelo Drift inicial.</small>
                  </div>
                </div>
              )}
              {v6.previsao_colapso_min && (
                <div className="modal-item" style={{borderColor: 'var(--danger)'}}>
                  <span className="icon">🛑</span>
                  <div>
                    <strong style={{color: 'var(--danger)'}}>Previsão de Falha</strong><br/>
                    <small>Ao manter a intensidade do último bloco com o Drift medido, o sistema saturaria em aprox. {v6.previsao_colapso_min} min.</small>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="modal-section">
            <h3>Biomecânica & Esforço</h3>
            <div className="modal-grid">
              <div className="modal-item">
                <span className="icon">⏱️</span>
                <div>
                  <strong>Velocidade & Pace:</strong><br/>
                  <small>Pace Médio: <strong>{formatPace(res.dist_km, res.tempo_s, res.pace_medio)} min/km</strong><br/>Grade Adj. Pace (GAP): <strong>{res.gap_pace || '--'} min/km</strong></small>
                </div>
              </div>
              <div className="modal-item">
                <span className="icon">❤️</span>
                <div>
                  <strong>Frequência Cardíaca:</strong><br/>
                  <small>Média: {formatNum(res.fc_media, 0)} bpm | Máx: {formatNum(res.fc_max, 0)}<br/>Recuperação: {formatNum(res.recuperacao_fc, 0)} bpm</small>
                </div>
              </div>
              <div className="modal-item">
                <span className="icon">⛰️</span>
                <div>
                  <strong>Altimetria & Terreno:</strong><br/>
                  <small>Ganho: +{formatNum(res.altimetria_ganho_m, 0)}m | Perda: -{formatNum(res.altimetria_perda_m, 0)}m</small>
                </div>
              </div>
              <div className="modal-item">
                <span className="icon">⚡</span>
                <div>
                  <strong>Energia & Potência:</strong><br/>
                  <small>Potência Estimada: {formatNum(res.potencia_media_w, 0)} W<br/>Custo Estimado: {res.calorias || '--'} kcal | Suor: {res.estimativa_suor_ml || '--'} ml</small>
                </div>
              </div>
            </div>
          </div>

          <div className="modal-section">
            <h3>Identidade dos Blocos (V6)</h3>
            <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
              {blocos.map((b, i) => (
                <div key={i} style={{background: 'rgba(255,255,255,0.02)', padding: '0.8rem', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                  <span style={{display: 'flex', flexDirection: 'column'}}>
                    <strong style={{textTransform: 'capitalize', color: b.tipo === 'corrida' ? 'var(--text-primary)' : 'var(--text-muted)'}}>{b.tipo}</strong>
                    <span style={{color: 'var(--accent-secondary)', fontSize: '0.85rem', fontWeight: 'bold'}}>{b.identidade?.toUpperCase()}</span>
                  </span>
                  <span style={{color: 'var(--text-secondary)', fontSize: '0.9rem', textAlign: 'right'}}>
                    {formatTempo(b.duracao_s)}<br/>
                    {formatNum(b.fc_media, 0)} bpm
                  </span>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>,
    document.body
  );
}
