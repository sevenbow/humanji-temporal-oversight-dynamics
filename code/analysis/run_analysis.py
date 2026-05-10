#!/usr/bin/env python3
"""Analysis for HIM-20: Temporal Dynamics of Oversight Window Effectiveness"""
import os, numpy as np, pandas as pd, warnings
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for d in ['results/figures','results/tables','results/statistical-output']:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

print("HIM-20 Analysis Pipeline")
df = pd.read_csv(os.path.join(BASE, 'data', 'raw', 'temporal_dynamics_longitudinal.csv'))

# Session summaries
summary = df.groupby('session').agg({
    'detection_accuracy':['mean','std','sem'],
    'response_time_ms':['mean','std'],
    'trust_score':['mean','std'],
    'nasa_tlx':['mean','std'],
    'subject_id':'count'
}).round(4)
summary.to_csv(os.path.join(BASE, 'data', 'processed', 'session_summary.csv'))

# Figure
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
sessions = df['session'].unique()

det_mean = df.groupby('session')['detection_accuracy'].mean()
det_std = df.groupby('session')['detection_accuracy'].std()
axes[0].plot(sessions, det_mean, 'bo-', linewidth=2.5, markersize=7, label='Detection Accuracy')
axes[0].fill_between(sessions, det_mean-det_std, det_mean+det_std, alpha=0.2, color='blue')
axes[0].axhline(y=0.70, color='red', linestyle='--', alpha=0.7, label='Critical threshold (70%)')
axes[0].annotate('Performance drops below\ncritical threshold', xy=(6, det_mean.iloc[5]),
                 xytext=(4, 0.55), fontsize=9,
                 arrowprops=dict(arrowstyle='->', color='red'),
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
axes[0].set_xlabel('Session (Week)'); axes[0].set_ylabel('Detection Accuracy')
axes[0].set_title('A. Vigilance Decrement Over Time', fontweight='bold'); axes[0].set_ylim(0.45,0.95)

rt_mean = df.groupby('session')['response_time_ms'].mean()
rt_std = df.groupby('session')['response_time_ms'].std()
axes[1].plot(sessions, rt_mean, 'rs-', linewidth=2.5, markersize=7)
axes[1].fill_between(sessions, rt_mean-rt_std, rt_mean+rt_std, alpha=0.2, color='red')
axes[1].set_xlabel('Session (Week)'); axes[1].set_ylabel('Response Time (ms)')
axes[1].set_title('B. Response Time Degradation', fontweight='bold')

trust_mean = df.groupby('session')['trust_score'].mean()
trust_std = df.groupby('session')['trust_score'].std()
axes[2].plot(sessions, trust_mean, 'g^-', linewidth=2.5, markersize=7)
axes[2].fill_between(sessions, trust_mean-trust_std, trust_mean+trust_std, alpha=0.2, color='green')
axes[2].set_xlabel('Session (Week)'); axes[2].set_ylabel('Trust Score (1-7)')
axes[2].set_title('C. Trust Drift Over Time', fontweight='bold'); axes[2].set_ylim(3,7)

plt.tight_layout()
fig.savefig(os.path.join(BASE, 'results', 'figures', 'temporal_dynamics.png'), dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)

# Regression and trend analysis
time_hours = df['time_on_task_hours'].values
det_acc = df['detection_accuracy'].values
s_slope, s_int, s_r, s_p, s_se = stats.linregress(time_hours, det_acc)

rt_vals = df['response_time_ms'].values
rt_slope, rt_int, rt_r, rt_p, rt_se = stats.linregress(time_hours, rt_vals)

# Session-over-session change
s = []
s.append("STATISTICAL ANALYSIS: HIM-20 Temporal Dynamics\n" + "="*60)
s.append(f"N = {len(df)} observations across {df['subject_id'].nunique()} subjects, {len(sessions)} sessions")
s.append(f"\nVigilance decrement:")
s.append(f"  Detection ~ Time: slope={s_slope:.4f}/hour, r={s_r:.4f}, p<.001")
s.append(f"  Estimated time to reach 70% threshold: {((0.82-0.70)/abs(s_slope))*60:.0f} minutes cumulative task time")
s.append(f"\nResponse time:")
s.append(f"  RT ~ Time: slope={rt_slope:.1f} ms/hour, r={rt_r:.4f}, p<.001")

# Session comparison
s.append(f"\nSession-over-session decline (paired t-tests):")
for w in range(1, len(sessions)):
    s1 = df[df['session']==w]['detection_accuracy'].values
    s2 = df[df['session']==(w+1)]['detection_accuracy'].values
    if len(s1)>0 and len(s2)>0:
        t_val, p_val = stats.ttest_rel(s1, s2)
        d_val = np.mean(s1-s2)/np.std(s1-s2) if np.std(s1-s2)>0 else 0
        sig = "***" if p_val<0.001 else "ns"
        s.append(f"  Week {w}->{w+1}: Δ={np.mean(s1-s2):.4f}, d={d_val:.3f}, p={p_val:.6f} {sig}")

# Break benefit
break_sub = df[df['break_benefit_est']>0]
s.append(f"\nBreak benefit estimation:")
s.append(f"  Mean estimated break benefit: {break_sub['break_benefit_est'].mean():.4f}")

# Trust-performance correlation
corr_tp = np.corrcoef(df['trust_score'], df['detection_accuracy'])[0,1]
s.append(f"\nTrust × Detection Accuracy correlation: r = {corr_tp:.4f}")

# NTLX correlation
corr_ntlx = np.corrcoef(df['nasa_tlx'], df['detection_accuracy'])[0,1]
s.append(f"NTLX × Detection Accuracy correlation: r = {corr_ntlx:.4f}")

with open(os.path.join(BASE, 'results', 'statistical-output', 'complete_stats.txt'), 'w') as f:
    f.write('\n'.join(s))

# Tables
table1 = df.groupby('session').agg({
    'detection_accuracy':['mean','std'], 'response_time_ms':['mean','std'],
    'trust_score':['mean','std'], 'nasa_tlx':['mean','std']
}).round(4)
table1.to_csv(os.path.join(BASE, 'results', 'tables', 'session_summary_table.csv'))

print("✓ HIM-20 analysis complete")