import React, { useState, useEffect, useMemo } from 'react';
import MonthlyCalendar from './MonthlyCalendar';
import DailyModal from './DailyModal';
import './Dashboard.css';

export default function Dashboard() {
  const [dailyData, setDailyData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [selectedDay, setSelectedDay] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/api/daily/todos')
      .then(res => res.json())
      .then(data => {
        setDailyData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError("Erro ao carregar dados do backend.");
        setLoading(false);
      });
  }, []);

  const handleSelectDay = (dayData) => {
    setSelectedDay(dayData);
    setIsModalOpen(true);
  };

  // ===== INSIGHTS MENSAIS =====
  const insights = useMemo(() => {
    if (!dailyData || dailyData.length === 0) return null;

    const last30 = dailyData.slice(-30);
    
    // Média HRV
    const hrvVals = last30.map(d => d.wearable?.hrv_ms).filter(v => v != null);
    const avgHrv = hrvVals.length > 0 ? Math.round(hrvVals.reduce((a,b) => a+b, 0) / hrvVals.length) : null;

    // Média RHR
    const rhrVals = last30.map(d => d.wearable?.rhr).filter(v => v != null);
    const avgRhr = rhrVals.length > 0 ? Math.round(rhrVals.reduce((a,b) => a+b, 0) / rhrVals.length) : null;

    // Consistência de Treino
    const diasComTreino = last30.filter(d => d.treino?.planejado !== 'Descanso');
    const diasExecutados = diasComTreino.filter(d => d.treino?.executado === 's');
    const consistencia = diasComTreino.length > 0 ? Math.round((diasExecutados.length / diasComTreino.length) * 100) : null;

    // Média Sono (horas)
    const sonoVals = last30.map(d => d.sono?.horas).filter(v => v != null);
    const avgSono = sonoVals.length > 0 ? (sonoVals.reduce((a,b) => a+b, 0) / sonoVals.length).toFixed(1) : null;

    // Média Readiness
    const readinessVals = last30.map(d => d.readiness).filter(v => v != null);
    const avgReadiness = readinessVals.length > 0 ? Math.round(readinessVals.reduce((a,b) => a+b, 0) / readinessVals.length) : null;

    return { avgHrv, avgRhr, consistencia, avgSono, avgReadiness, totalDias: last30.length };
  }, [dailyData]);

  if (loading) return <div className="container flex items-center justify-center" style={{height: '100vh'}}><h2>Carregando Painel Elite...</h2></div>;
  if (error) return <div className="container"><h2 style={{color: 'var(--danger)'}}>{error}</h2></div>;

  const last7Days = dailyData.slice(-7);
  const avgScore = last7Days.length > 0 
    ? Math.round(last7Days.reduce((acc, curr) => acc + curr.score, 0) / last7Days.length)
    : 0;

  return (
    <div className="container animate-fade-in">
      <header className="dashboard-header flex justify-between items-center">
        <div>
          <h1 className="text-gradient">Py-Fit Elite</h1>
          <p className="text-secondary">Visão Sistêmica Mensal</p>
        </div>
        <div className="glass-card score-badge" title="Média dos últimos 7 dias logados">
          <span className="score-label">Score 7D</span>
          <span className="score-value">{avgScore}</span>
        </div>
      </header>

      <div className="grid" style={{ gap: '2rem' }}>
        {/* Painel Central Único para o Calendário */}
        <section className="glass-card section-card" style={{ maxWidth: '800px', margin: '0 auto', width: '100%' }}>
          <h2>Histórico Mensal</h2>
          <MonthlyCalendar 
            data={dailyData} 
            onSelectDay={handleSelectDay}
            selectedDateStr={null} 
          />
        </section>
        
        {/* Insights Mensais V6 */}
        {insights && (
          <section className="glass-card section-card" style={{ maxWidth: '800px', margin: '0 auto', width: '100%' }}>
            <h2>📊 Insights do Período ({insights.totalDias} dias)</h2>
            <div className="insights-grid">
              {insights.avgReadiness !== null && (
                <div className="insight-card">
                  <span className="insight-icon">🧬</span>
                  <span className="insight-value" style={{color: insights.avgReadiness >= 75 ? 'var(--success)' : insights.avgReadiness >= 50 ? 'var(--warning)' : 'var(--danger)'}}>
                    {insights.avgReadiness}
                  </span>
                  <span className="insight-label">Readiness Médio</span>
                </div>
              )}
              {insights.avgHrv !== null && (
                <div className="insight-card">
                  <span className="insight-icon">❤️</span>
                  <span className="insight-value">{insights.avgHrv} <small>ms</small></span>
                  <span className="insight-label">HRV Médio</span>
                </div>
              )}
              {insights.avgRhr !== null && (
                <div className="insight-card">
                  <span className="insight-icon">💓</span>
                  <span className="insight-value">{insights.avgRhr} <small>bpm</small></span>
                  <span className="insight-label">RHR Médio</span>
                </div>
              )}
              {insights.avgSono !== null && (
                <div className="insight-card">
                  <span className="insight-icon">💤</span>
                  <span className="insight-value">{insights.avgSono} <small>h</small></span>
                  <span className="insight-label">Sono Médio</span>
                </div>
              )}
              {insights.consistencia !== null && (
                <div className="insight-card">
                  <span className="insight-icon">🎯</span>
                  <span className="insight-value" style={{color: insights.consistencia >= 80 ? 'var(--success)' : insights.consistencia >= 60 ? 'var(--warning)' : 'var(--danger)'}}>
                    {insights.consistencia}%
                  </span>
                  <span className="insight-label">Consistência Treino</span>
                </div>
              )}
            </div>
          </section>
        )}
      </div>

      {isModalOpen && (
        <DailyModal 
          data={selectedDay} 
          onClose={() => setIsModalOpen(false)} 
        />
      )}
    </div>
  );
}
