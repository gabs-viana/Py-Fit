import React, { useState, useEffect } from 'react';
import RunModal from './RunModal';
import './RunLab.css';

export default function RunLab() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [selectedRun, setSelectedRun] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/api/fit/runs')
      .then(res => res.json())
      .then(data => {
        setRuns(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError("Erro ao carregar os dados do Fit Analyzer.");
        setLoading(false);
      });
  }, []);

  const handleRunClick = (run) => {
    setSelectedRun(run);
    setIsModalOpen(true);
  };

  const getDominanciaColor = (status) => {
    if (!status) return 'var(--text-muted)';
    if (status.includes('verde')) return 'var(--success)';
    if (status.includes('amarelo')) return 'var(--warning)';
    if (status.includes('vermelho')) return 'var(--danger)';
    return 'var(--text-muted)';
  };

  const formatDate = (id) => {
    // id = Zepp20260505191304.json
    const match = id.match(/Zepp(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})/);
    if (match) {
      return `${match[3]}/${match[2]}/${match[1]} ${match[4]}:${match[5]}`;
    }
    return id;
  };

  const formatNum = (num, decimals = 1) => {
    if (num === null || num === undefined) return '--';
    if (typeof num === 'number') return Number(num).toFixed(decimals);
    // Se for string, tenta converter, mas devolve original em caso de falha
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

  if (loading) return <div className="container flex items-center justify-center" style={{height: '100vh'}}><h2>Carregando Fisiologia...</h2></div>;
  if (error) return <div className="container"><h2 style={{color: 'var(--danger)'}}>{error}</h2></div>;

  return (
    <div className="container animate-fade-in">
      <header className="dashboard-header flex justify-between items-center" style={{marginBottom: '2rem'}}>
        <div>
          <h1 className="text-gradient">Run Lab</h1>
          <p className="text-secondary">Laboratório Biomecânico & Fisiológico V6</p>
        </div>
        <div className="glass-card score-badge" style={{background: 'rgba(79, 70, 229, 0.1)', borderColor: 'var(--accent-primary)'}}>
          <span className="score-label" style={{color: 'var(--text-primary)'}}>Treinos Logados</span>
          <span className="score-value" style={{color: 'var(--accent-primary)'}}>{runs.length}</span>
        </div>
      </header>

      {runs.length === 0 ? (
        <div className="glass-card section-card" style={{textAlign: 'center', padding: '4rem'}}>
          <p style={{color: 'var(--text-muted)'}}>Nenhum treino encontrado na pasta Fit Analyzer.</p>
        </div>
      ) : (
        <div className="runs-grid">
          {runs.map(run => {
            const v6 = run.v6_elite || {};
            const res = run.resumo || {};
            const domColor = getDominanciaColor(v6.dominancia_simpatica);

            return (
              <div 
                key={run.id} 
                className="run-card glass-card"
                onClick={() => handleRunClick(run)}
              >
                <div className="run-card-header">
                  <span className="run-date">{formatDate(run.id)}</span>
                  <span className="run-type" style={{color: 'var(--accent-secondary)'}}>{run.avaliacao?.tipo_treino_detectado?.toUpperCase() || 'TREINO'}</span>
                </div>
                
                <div className="run-stats-main">
                  <div>
                    <span className="stat-value">{formatNum(res.dist_km, 2)} <small>km</small></span>
                  </div>
                  <div>
                    <span className="stat-value">{formatPace(res.dist_km, res.tempo_s, res.pace_medio)} <small>min/km</small></span>
                  </div>
                  <div>
                    <span className="stat-value" style={{color: domColor}}>{formatNum(res.fc_media, 0)} <small>bpm</small></span>
                  </div>
                </div>

                <div className="run-v6-highlights">
                  {v6.dominancia_simpatica && (
                    <div className="v6-badge" style={{borderColor: domColor, color: domColor}}>
                      Autonômico: {v6.dominancia_simpatica.split(' ')[0].toUpperCase()}
                    </div>
                  )}
                  {v6.pacing_emocional_detectado && (
                    <div className="v6-badge" style={{borderColor: 'var(--warning)', color: 'var(--warning)'}}>
                      ⚠️ Pacing Emocional
                    </div>
                  )}
                  {v6.tempo_fluxo_util_min > 0 && (
                    <div className="v6-badge" style={{borderColor: 'var(--accent-primary)', color: 'var(--accent-primary)'}}>
                      🔥 Fluxo Útil: {v6.tempo_fluxo_util_min} min
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {isModalOpen && (
        <RunModal run={selectedRun} onClose={() => setIsModalOpen(false)} />
      )}
    </div>
  );
}
