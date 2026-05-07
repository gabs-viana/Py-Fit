import React from 'react';
import './WeeklyHeatmap.css';

export default function WeeklyHeatmap({ data }) {
  // Dias da semana 0 a 6
  const diasDaSemana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];
  
  // Array de 7 posições
  const weekBlocks = Array(7).fill(null);
  
  data.forEach(d => {
    // Extrai o dia da semana pela data DD/MM/YYYY
    const parts = d.data.split('/');
    if(parts.length === 3) {
      const dateObj = new Date(parts[2], parts[1]-1, parts[0]);
      let wd = dateObj.getDay(); 
      wd = wd === 0 ? 6 : wd - 1; // Transforma para 0=Seg, 6=Dom
      weekBlocks[wd] = d;
    }
  });

  const getScoreClass = (score) => {
    if(!score) return 'score-none';
    if(score >= 850) return 'score-elite';
    if(score >= 700) return 'score-forte';
    if(score >= 550) return 'score-boa';
    if(score >= 400) return 'score-regular';
    return 'score-fraca';
  };

  return (
    <div className="heatmap-container">
      {weekBlocks.map((dayData, idx) => {
        const score = dayData ? dayData.score : 0;
        const colorClass = getScoreClass(score);
        return (
          <div key={idx} className="heatmap-day">
            <div className={`heatmap-block ${colorClass}`} title={dayData ? `Score: ${score}` : 'Sem dados'}>
              {score > 0 && <span className="block-score">{score}</span>}
            </div>
            <span className="day-label">{diasDaSemana[idx]}</span>
          </div>
        )
      })}
    </div>
  );
}
