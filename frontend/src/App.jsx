import React,{useEffect,useState} from 'react'
import {LineChart,Line,BarChart,Bar,XAxis,YAxis,Tooltip,Legend,ResponsiveContainer} from 'recharts'
const f=(x)=>Math.round(x).toLocaleString()
export default function App(){
  const [cut,setCut]=useState(9); const [d,setD]=useState(null); const [day,setDay]=useState('2026-01-15')
  useEffect(()=>{setD(null);fetch(`/api/data?cutoff_hour=${cut}`).then(r=>r.json()).then(setD)},[cut])
  if(!d) return <p style={{padding:24}}>Loading Elexon data…</p>
  const m=d.metrics, rows=d.rows.filter(r=>r.startTime.startsWith(day)).map(r=>({t:r.startTime.slice(11,16),...r}))
  const Card=({k,v,u='MW'})=><div style={{border:'1px solid #ddd',borderRadius:8,padding:12,minWidth:130}}><small>{k}</small><h3 style={{margin:0}}>{v} {u}</h3></div>
  return <div style={{fontFamily:'sans-serif',padding:24,maxWidth:1100,margin:'auto'}}>
    <h1>Wind Day-Ahead Forecast Evaluator – Jan 2026</h1>
    <p>Forecast used = latest WINDFOR published before the day-ahead cutoff (D-1, <input type="number" min="0" max="23" value={cut} onChange={e=>setCut(+e.target.value)} style={{width:50}}/>:00 UTC) vs FUELHH actual wind.</p>
    <div style={{display:'flex',gap:12,flexWrap:'wrap'}}>
      <Card k="MAE" v={f(m.mae)}/><Card k="RMSE" v={f(m.rmse)}/><Card k="Bias (fcst−actual)" v={f(m.bias)}/>
      <Card k="95th pct abs error" v={f(m.p95_abs_error)}/><Card k="MAPE" v={m.mape_pct.toFixed(1)} u="%"/></div>
    <h3>Forecast vs actual – <input type="date" min="2026-01-01" max="2026-01-31" value={day} onChange={e=>setDay(e.target.value)}/></h3>
    <ResponsiveContainer width="100%" height={300}><LineChart data={rows}><XAxis dataKey="t"/><YAxis/><Tooltip/><Legend/>
      <Line dataKey="forecast" stroke="#2563eb" dot={false}/><Line dataKey="actual" stroke="#16a34a" dot={false}/></LineChart></ResponsiveContainer>
    <h3>Daily MAE (MW)</h3>
    <ResponsiveContainer width="100%" height={220}><BarChart data={d.daily}><XAxis dataKey="day" tickFormatter={s=>s.slice(8)}/><YAxis/><Tooltip/><Bar dataKey="mae" fill="#f59e0b"/></BarChart></ResponsiveContainer>
    <p><b>How to use:</b> residual load to buy = demand − wind forecast; add ± P95 error as a buffer.</p>
  </div>}
