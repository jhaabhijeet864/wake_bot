"""
WakeBot Calibration Command
Enhanced calibration with automatic clap detection and precise threshold calculation.
"""

import time
import sys
import numpy as np
from collections import deque
from typing import List, Tuple
from wakebot.core import WakeBotLogger
from wakebot.triggers.audio.engine import AudioStream


def detect_claps(rms_values: List[float], timestamps: List[float], 
                 threshold_preview: float = 1000) -> List[Tuple[float, float]]:
    """Detect clap peaks in RMS data"""
    claps = []
    if len(rms_values) < 10:
        return claps
    
    window_size = 5
    for i in range(window_size, len(rms_values) - window_size):
        current_rms = rms_values[i]
        if current_rms > threshold_preview:
            is_peak = True
            for j in range(i - window_size, i + window_size + 1):
                if j != i and rms_values[j] >= current_rms:
                    is_peak = False
                    break
            
            if is_peak:
                if not claps or (timestamps[i] - claps[-1][0]) > 0.3:
                    claps.append((timestamps[i], current_rms))
    return claps


def run_calibrate():
    """Enhanced calibration tool implementation"""
    logger = WakeBotLogger()
    
    print("\n" + "="*70)
    print(" " * 15 + "WakeBot Enhanced Calibration Tool")
    print("="*70)
    print("\n📋 CALIBRATION INSTRUCTIONS:")
    print("   Phase 1: Establish Baseline (10 seconds)")
    print("   Phase 2: Record Claps (30+ seconds)")
    print("   Phase 3: Analysis")
    print("="*70 + "\n")
    
    input("Press ENTER when ready to start calibration...")
    print()
    
    audio = AudioStream()
    
    try:
        if not audio.start_stream():
            logger.error("Failed to initialize microphone.")
            return
        
        logger.info("🎤 Microphone initialized successfully")
        
        # Collect RMS values
        rms_values: List[float] = []
        timestamps: List[float] = []
        min_rms = float('inf')
        max_rms = 0.0
        total_rms = 0.0
        sample_count = 0
        
        detected_clap_count = 0
        detected_claps_realtime: List[Tuple[float, float]] = []
        
        start_time = time.time()
        current_phase = 1
        baseline_max = 0
        
        print("⏱️  Phase 1: Measuring ambient noise baseline (10 seconds)...\n")
        
        try:
            while True:
                chunk = audio.read_chunk()
                rms = audio.calculate_rms(chunk)
                current_time = time.time()
                elapsed = current_time - start_time
                
                rms_values.append(rms)
                timestamps.append(elapsed)
                min_rms = min(min_rms, rms)
                max_rms = max(max_rms, rms)
                total_rms += rms
                sample_count += 1
                
                if current_phase == 1:
                    baseline_max = max(baseline_max, rms)
                    if elapsed >= 10:
                        current_phase = 2
                        print(f"\n✅ Baseline established! Max baseline RMS: {baseline_max:.0f}")
                        print(f"⏱️  Phase 2: Clap 5-10 times (Press Ctrl+C when done)\n")
                
                if current_phase == 2:
                    # Simple peak detection for feedback
                    if rms > baseline_max * 2.5 and rms > 100:
                        # Simple debounce
                        if not detected_claps_realtime or (elapsed - detected_claps_realtime[-1][0] > 0.5):
                            detected_clap_count += 1
                            detected_claps_realtime.append((elapsed, rms))
                            print(f"\n   👏 Clap #{detected_clap_count} detected! (RMS: {rms:.0f})")
                
                status = f"\rPhase: {current_phase} | RMS: {rms:6.0f} | Claps: {detected_clap_count}"
                print(status, end='', flush=True)
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print(f"\n\nStopping calibration...")
        
        audio.stop_stream()
        
        # Analysis (Simplified version of the full analysis)
        if sample_count > 0:
            avg_rms = total_rms / sample_count
            print("\n" + "="*70)
            print(" " * 15 + "📊 CALIBRATION ANALYSIS RESULTS")
            print("="*70)
            print(f"   Max Baseline:    {baseline_max:.0f}")
            print(f"   Max Peak:        {max_rms:.0f}")
            print(f"   Claps Detected:  {detected_clap_count}")
            
            if detected_clap_count > 0:
                clap_avg = sum(c[1] for c in detected_claps_realtime) / detected_clap_count
                recommended = int(clap_avg * 0.5)
                recommended = max(recommended, int(baseline_max * 2))
                print(f"\n🎯 RECOMMENDED THRESHOLD: {recommended}")
            else:
                recommended = int(baseline_max * 2.5)
                print(f"\n🎯 RECOMMENDED THRESHOLD (Baseline fallback): {recommended}")
            
            print("\n📝 Edit 'wakebot_config.json' and set 'threshold' to the value above.")
            print("="*70 + "\n")
            
    except Exception as e:
        logger.error(f"Calibration failed: {e}")
        audio.stop_stream()
