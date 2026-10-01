from pathlib import Path
from datetime import datetime
import io
import json
import shutil
import uuid
import zipfile
import pandas as pd
import plotly.express as px
import streamlit as st
from retailflow.engine import validate_config
from retailflow.demo import generate

ROOT=Path(__file__).parent
OUTPUT=ROOT/'outputs'; OUTPUT.mkdir(exist_ok=True)
st.set_page_config(page_title='RetailFlow AI',page_icon='◈',layout='wide')
st.title('RetailFlow AI')
st.caption('SMART RETAIL VISION • Footfall, movement and queue intelligence')


def bundle(folder):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
        for p in Path(folder).glob('*'):
            if p.is_file() and p.suffix in ('.csv','.json'): z.write(p,p.name)
    return b.getvalue()


def dashboard(folder):
    folder=Path(folder)
    m=pd.read_csv(folder/'minute_metrics.csv',parse_dates=['minute'])
    visits=pd.read_csv(folder/'zone_visits.csv')
    meta=json.loads((folder/'metadata.json').read_text())
    if meta['source_type']=='synthetic_demo': st.warning('SYNTHETIC DEMO — simulated trajectories, not real customer or model results.')
    if m.empty:
        st.info('No time intervals were recorded.'); return
    times=m['minute'].sort_values().unique()
    if len(times)>1:
        selected=st.select_slider('Time window',options=list(range(len(times))),value=(0,len(times)-1),format_func=lambda i:pd.Timestamp(times[i]).strftime('%H:%M'),key=str(folder))
        m=m[(m.minute>=times[selected[0]])&(m.minute<=times[selected[1]])]
        lower=pd.Timestamp(times[selected[0]]); upper=pd.Timestamp(times[selected[1]])+pd.Timedelta(minutes=1)
        if not visits.empty:
            entered=pd.to_datetime(visits.entered_at)
            visits=visits[(entered>=lower)&(entered<upper)]
        st.caption('Visit charts use visits that started in the selected window; duration may extend beyond it.')
    observed=m.observed_seconds.sum()
    cols=st.columns(4)
    cols[0].metric('Entry crossings',int(m.entries.sum()))
    cols[1].metric('Exit crossings',int(m.exits.sum()))
    cols[2].metric('Average visible people',f'{m.person_seconds.sum()/observed:.1f}' if observed else '—')
    cols[3].metric('Queue alerts',int(m.queue_alerts.sum()))
    left,right=st.columns(2)
    left.plotly_chart(px.line(m,x='minute',y=['entries','exits'],title='Doorway activity'),use_container_width=True)
    chart=m.assign(avg_queue=m.queue_person_seconds/m.observed_seconds.replace(0,float('nan')))
    right.plotly_chart(px.line(chart,x='minute',y=['avg_queue','peak_queue'],title='Queue-zone occupancy'),use_container_width=True)
    if not visits.empty:
        completed=visits[(visits.left_censored==False)&(visits.right_censored==False)]
        counts=visits.groupby('zone').size().reset_index(name='observed_visits')
        left.plotly_chart(px.bar(counts,x='zone',y='observed_visits',title='Observed zone visits (includes partial visits)'),use_container_width=True)
        if not completed.empty:
            right.plotly_chart(px.box(completed,x='zone',y='duration_s',title='Fully observed visit duration'),use_container_width=True)
        else: right.info('No fully observed zone visits in this window.')
    pos=pd.read_csv(folder/'positions.csv')
    if not pos.empty:
        stamp=pd.to_datetime(pos.timestamp)
        pos=pos[(stamp>=m.minute.min())&(stamp<m.minute.max()+pd.Timedelta(minutes=1))]
        if not pos.empty:
            fig=px.density_heatmap(pos,x='x',y='y',nbinsx=24,nbinsy=16,title='Image-space presence • observed track samples',color_continuous_scale='Teal')
            fig.update_yaxes(autorange='reversed'); fig.update_xaxes(range=[0,1]); fig.update_yaxes(range=[1,0])
            st.plotly_chart(fig,use_container_width=True)
    st.caption('Counts describe anonymous tracks and crossings, not distinct shoppers. Queue-zone duration is a proxy; staff may be included.')
    st.download_button('Download Tableau CSV bundle',bundle(folder),file_name=folder.name+'_tableau.zip',mime='application/zip')
    annotated=folder/'annotated.avi'
    if annotated.exists():
        st.download_button('Download annotated video (AVI)',annotated.read_bytes(),file_name='annotated.avi',mime='video/x-msvideo')
    with st.expander('Run details and data preview'):
        st.json(meta); st.dataframe(m,use_container_width=True)

mode=st.sidebar.radio('Workspace',['Demo dashboard','Analyze video','Saved runs','Tableau guide'])
st.sidebar.caption('Local processing • Anonymous track IDs • Single camera per run')
if mode=='Demo dashboard':
    demo=ROOT/'data/demo'
    if not (demo/'metadata.json').exists(): generate(json.loads((ROOT/'config/store.json').read_text()),demo)
    dashboard(demo)
elif mode=='Analyze video':
    st.subheader('Analyze a store recording')
    st.write('Upload a fixed-camera, constant-frame-rate video. Align the gate and zones with the camera before processing.')
    uploaded=st.file_uploader('Video',type=['mp4','avi','mov','mkv'])
    config_text=st.text_area('Store configuration — normalized coordinates from 0 to 1',value=(ROOT/'config/store.json').read_text(),height=270)
    st.caption('x: left → right; y: top → bottom. Gate entry_direction −1 means decreasing coordinate. Zones use the bottom-centre of each person box.')
    a,b,c=st.columns(3)
    start=a.text_input('Recording start (local time)','2026-10-01T10:00:00')
    device=b.selectbox('Inference device',['cpu','0'])
    seconds=c.number_input('Maximum seconds to process',min_value=1,max_value=3600,value=60)
    model=st.text_input('Model weights','yolo11n.pt',help='Downloads on first use. For your fine-tuned model, enter the path to best.pt.')
    conf=st.slider('Detection confidence',.1,.9,.3,.05)
    save_video=st.checkbox('Save annotated video',True)
    if uploaded is not None:
        import cv2
        source=OUTPUT/('upload_'+str(uuid.uuid4())+Path(uploaded.name).suffix.lower())
        # Save only on explicit preview/process; no file writes on slider changes.
        if st.button('Preview gate and zones'):
            try:
                config=validate_config(json.loads(config_text))
                source.write_bytes(uploaded.getbuffer())
                cap=cv2.VideoCapture(str(source)); ok,frame=cap.read(); cap.release()
                if not ok: raise ValueError('Could not decode the first frame.')
                from retailflow.video import overlay
                st.image(cv2.cvtColor(overlay(frame,config),cv2.COLOR_BGR2RGB),caption='Adjust config above to match your actual layout.',use_container_width=True)
            except Exception as e: st.error(str(e))
            finally: source.unlink(missing_ok=True)
        if st.button('Run video analysis',type='primary'):
            run=OUTPUT/('video_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6])
            try:
                config=validate_config(json.loads(config_text)); datetime.fromisoformat(start)
                source.write_bytes(uploaded.getbuffer())
                bar=st.progress(0,text='Loading detector / processing video…')
                from retailflow.video import analyze_video
                with st.spinner('Processing every frame. CPU processing may take longer than video duration.'):
                    analyze_video(source,config,run,start,model,conf,device,int(seconds),lambda x:bar.progress(min(x,1.)),save_video)
                st.session_state['last_run']=str(run)
                st.success('Analysis complete. CSV exports and run metadata are ready.')
            except Exception as e:
                st.error(f'Analysis failed: {e}')
                st.info('Check model download access, the video codec and requirements. GPU device 0 requires a compatible CUDA PyTorch installation.')
                if run.exists(): shutil.rmtree(run)
            finally: source.unlink(missing_ok=True)
    if st.session_state.get('last_run') and Path(st.session_state['last_run']).exists(): dashboard(st.session_state['last_run'])
elif mode=='Saved runs':
    runs=sorted([p for p in OUTPUT.iterdir() if p.is_dir() and (p/'metadata.json').exists()],reverse=True)
    if runs: dashboard(st.selectbox('Run',runs,format_func=lambda p:p.name))
    else: st.info('Analyze a video to create your first saved run.')
else:
    st.markdown((ROOT/'docs/TABLEAU_GUIDE.md').read_text())
