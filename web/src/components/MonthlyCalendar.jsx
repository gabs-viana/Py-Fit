import React, { useState, useEffect, useMemo } from 'react';
import './MonthlyCalendar.css';

export default function MonthlyCalendar({ data, onSelectDay, selectedDateStr }) {
  const [currentDate, setCurrentDate] = useState(new Date());

  // Inicia o calendário no mês do dado mais recente
  useEffect(() => {
    if (data && data.length > 0) {
      const lastEntry = data[data.length - 1];
      const parts = lastEntry.data.split('/');
      if (parts.length === 3) {
        setCurrentDate(new Date(parts[2], parts[1] - 1, 1));
      }
    }
  }, [data]);

  const prevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const daysInMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0).getDate();
  const firstDayOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1).getDay();
  
  // Ajuste para semana começar na Segunda-feira (Seg=0, Dom=6)
  const startDay = firstDayOfMonth === 0 ? 6 : firstDayOfMonth - 1;

  const monthNames = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
  ];

  const getScoreClass = (score) => {
    if (!score) return 'score-none';
    if (score >= 850) return 'score-elite';
    if (score >= 700) return 'score-forte';
    if (score >= 550) return 'score-boa';
    if (score >= 400) return 'score-regular';
    return 'score-fraca';
  };

  const dataMap = useMemo(() => {
    const map = {};
    data.forEach(d => {
      map[d.data] = d;
    });
    return map;
  }, [data]);

  const blocks = [];
  
  // Células vazias iniciais
  for (let i = 0; i < startDay; i++) {
    blocks.push(<div key={`empty-${i}`} className="calendar-block empty"></div>);
  }

  // Dias do mês
  for (let d = 1; d <= daysInMonth; d++) {
    const dayStr = String(d).padStart(2, '0');
    const monthStr = String(currentDate.getMonth() + 1).padStart(2, '0');
    const yearStr = currentDate.getFullYear();
    const dateKey = `${dayStr}/${monthStr}/${yearStr}`;
    
    const dayData = dataMap[dateKey];
    const score = dayData ? dayData.score : null;
    const colorClass = getScoreClass(score);
    const isSelected = selectedDateStr === dateKey;

    blocks.push(
      <div 
        key={d} 
        className={`calendar-block ${colorClass} ${isSelected ? 'selected' : ''} ${dayData ? 'clickable' : ''}`}
        onClick={() => {
          if (dayData) onSelectDay(dayData);
        }}
        title={dayData ? `Score: ${score}` : 'Sem dados'}
      >
        <span className="calendar-day-number">{d}</span>
        {score > 0 && <span className="calendar-score">{score}</span>}
      </div>
    );
  }

  return (
    <div className="monthly-calendar">
      <div className="calendar-header flex justify-between items-center">
        <button className="nav-btn" onClick={prevMonth}>&lt;</button>
        <h3>{monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}</h3>
        <button className="nav-btn" onClick={nextMonth}>&gt;</button>
      </div>
      <div className="calendar-grid-header">
        <span>Seg</span><span>Ter</span><span>Qua</span><span>Qui</span><span>Sex</span><span>Sáb</span><span>Dom</span>
      </div>
      <div className="calendar-grid">
        {blocks}
      </div>
    </div>
  );
}
