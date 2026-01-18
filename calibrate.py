"""
Calibration Tool for WakeBot

Enhanced calibration with automatic clap detection and precise threshold calculation.

Instructions:
1. Sit quietly for 5-10 seconds to establish ambient noise baseline
2. Clap loudly 5-10 times with 2-3 second gaps between claps
3. The tool will automatically detect and analyze your claps
4. Press Ctrl+C when done to see detailed recommendations
"""

import sys
import time
import numpy as np
from collections import deque
from typing import List, Tuple

# Add src to path
sys.path.insert(0, '.')

from src.audio_engine import AudioStream
from src.logger import WakeBotLogger


def detect_claps(rms_values: List[float], timestamps: List[float], 
                 threshold_preview: float = 1000) -> List[Tuple[float, float]]:
    """
    Detect clap peaks in RMS data
    
    Returns:
        List of (timestamp, rms_value) tuples for detected claps
    """
    claps = []
    if len(rms_values) < 10:
        return claps
    
    # Use a rolling window to find peaks
    window_size = 5
    for i in range(window_size, len(rms_values) - window_size):
        current_rms = rms_values[i]
        
        # Check if this is a peak above threshold
        if current_rms > threshold_preview:
            # Check if it's higher than surrounding values (peak detection)
            is_peak = True
            for j in range(i - window_size, i + window_size + 1):
                if j != i and rms_values[j] >= current_rms:
                    is_peak = False
                    break
            
            if is_peak:
                # Avoid duplicates (claps are typically spread out)
                if not claps or (timestamps[i] - claps[-1][0]) > 0.3:
                    claps.append((timestamps[i], current_rms))
    
    return claps


def main():
    """Enhanced calibration tool with automatic clap detection"""
    logger = WakeBotLogger()
    
    print("\n" + "="*70)
    print(" " * 15 + "WakeBot Enhanced Calibration Tool")
    print("="*70)
    print("\n📋 CALIBRATION INSTRUCTIONS:")
    print("   Phase 1: Establish Baseline (10 seconds)")
    print("   ├─ Sit quietly, don't move")
    print("   ├─ Let the tool measure your ambient noise")
    print("   └─ Observe the RMS values (should be low and steady)\n")
    print("   Phase 2: Record Claps (30+ seconds)")
    print("   ├─ Clap loudly and clearly 5-10 times")
    print("   ├─ Wait 2-3 seconds between each clap")
    print("   ├─ Clap near your microphone/laptop")
    print("   └─ The tool will detect and highlight each clap automatically\n")
    print("   Phase 3: Analysis")
    print("   └─ Press Ctrl+C when done to see recommendations\n")
    print("="*70 + "\n")
    
    input("Press ENTER when ready to start calibration...")
    print()
    
    # Initialize audio engine
    audio = AudioStream()
    
    try:
        if not audio.start_stream():
            logger.error("Failed to initialize microphone. Check permissions.")
            return
        
        logger.info("🎤 Microphone initialized successfully")
        
        # ===== MICROPHONE TEST PHASE =====
        print("\n" + "="*70)
        print(" " * 20 + "🎤 MICROPHONE TEST")
        print("="*70)
        print("\nThis test verifies your microphone is working before calibration.")
        print("Watch the RMS values - they should INCREASE when you make sound.\n")
        input("Press ENTER to start microphone test (5 seconds)...")
        print()
        
        test_samples = []
        test_start = time.time()
        test_duration = 5.0
        test_max_rms = 0
        test_quiet_max = 0
        test_sound_detected = False
        
        print("📊 Listening for 5 seconds...")
        print("   └─ Make a sound (clap, tap, or speak) to test the microphone\n")
        
        quiet_period_end = None
        while time.time() - test_start < test_duration:
            try:
                chunk = audio.read_chunk()
                rms = audio.calculate_rms(chunk)
                test_samples.append(rms)
                test_max_rms = max(test_max_rms, rms)
                
                elapsed_test = time.time() - test_start
                remaining = test_duration - elapsed_test
                
                # Track quiet period (first 2 seconds)
                if elapsed_test < 2.0:
                    test_quiet_max = max(test_quiet_max, rms)
                
                # Check if we detected significant sound (3x quiet max)
                if elapsed_test >= 2.0 and rms > test_quiet_max * 3 and rms > 20:
                    test_sound_detected = True
                
                # Visual indicator bar
                bar_length = 50
                bar_fill = int((elapsed_test / test_duration) * bar_length)
                bar = "█" * bar_fill + "░" * (bar_length - bar_fill)
                
                # Color code RMS values
                rms_indicator = "🔴" if rms < 5 else "🟡" if rms < 50 else "🟢"
                
                status_line = f"\r⏱️  [{bar}] {remaining:.1f}s | RMS: {rms:6.0f} {rms_indicator}"
                if test_sound_detected and elapsed_test >= 2.0:
                    status_line += " ✅ Sound detected!"
                
                print(status_line, end='', flush=True)
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error during test: {e}")
                break
        
        print("\n\n" + "─"*70)
        
        # Analyze test results
        test_avg = sum(test_samples) / len(test_samples) if test_samples else 0
        test_min = min(test_samples) if test_samples else 0
        
        print("📊 MICROPHONE TEST RESULTS:")
        print(f"   Minimum RMS:      {test_min:.0f}")
        print(f"   Maximum RMS:      {test_max_rms:.0f}")
        print(f"   Average RMS:      {test_avg:.0f}")
        print(f"   Quiet period max: {test_quiet_max:.0f}")
        
        if test_max_rms < 5:
            print("\n❌ MICROPHONE NOT WORKING!")
            print("   └─ RMS values are too low (< 5). Microphone may not be working.")
            print("\n🔧 TROUBLESHOOTING:")
            print("   1. Check microphone permissions (Windows Settings → Privacy → Microphone)")
            print("   2. Check if microphone is muted in system settings")
            print("   3. Try a different microphone")
            print("   4. Restart the calibration tool")
            audio.stop_stream()
            return
        elif test_max_rms < 20:
            print("\n⚠️  MICROPHONE SEEMS QUIET")
            print("   └─ RMS values are very low. You may need to clap louder.")
            print("   └─ Try increasing microphone volume in system settings.")
            response = input("\nContinue anyway? (y/n): ").lower()
            if response != 'y':
                audio.stop_stream()
                return
        elif not test_sound_detected:
            print("\n⚠️  NO SIGNIFICANT SOUND DETECTED")
            print(f"   └─ Maximum RMS was {test_max_rms:.0f}, but no clear sound spike detected.")
            print("   └─ Make sure to clap LOUDLY during Phase 2!")
            response = input("\nContinue anyway? (y/n): ").lower()
            if response != 'y':
                audio.stop_stream()
                return
        else:
            print("\n✅ MICROPHONE WORKING!")
            print(f"   └─ Detected sound with RMS up to {test_max_rms:.0f}")
        
        print("="*70 + "\n")
        input("Press ENTER to proceed to calibration...")
        print("\n📊 Starting calibration...\n")
        
        # Store test results for use in Phase 2 threshold calculation
        mic_test_max_rms = test_max_rms  # Store for later use
        
        # Collect RMS values with timestamps
        rms_values: List[float] = []
        timestamps: List[float] = []
        min_rms = float('inf')
        max_rms = 0.0
        total_rms = 0.0
        sample_count = 0
        
        # Keep last 50 values for rolling average
        recent_values = deque(maxlen=50)
        
        # Clap detection during calibration
        last_clap_detection = 0
        detected_clap_count = 0
        detected_claps_realtime: List[Tuple[float, float]] = []  # (timestamp, rms)
        
        start_time = time.time()
        phase_start = start_time
        phase2_start = None
        current_phase = 1
        phase2_duration = 0
        phase2_max_duration = 45  # Max 45 seconds for Phase 2
        target_claps = 6  # Auto-end after detecting this many claps
        baseline_max = 0
        low_rms_warned = False  # Flag to warn only once about low RMS
        
        # Verify stream is active before starting
        if not audio.is_stream_active():
            logger.error("⚠️  Audio stream is not active! Attempting to restart...")
            if not audio.restart_stream():
                logger.error("❌ Failed to restart audio stream. Exiting.")
                return
            logger.info("✅ Stream restarted successfully")
        
        print("⏱️  Phase 1: Measuring ambient noise baseline (10 seconds)...\n")
        
        try:
            while True:
                # Check stream status periodically
                if not audio.is_stream_active():
                    logger.error("⚠️  Stream became inactive! Attempting restart...")
                    if not audio.restart_stream():
                        logger.error("❌ Failed to restart stream.")
                        break
                
                chunk = audio.read_chunk()
                
                # Debug: Check if chunk is all zeros or suspiciously small
                if len(chunk) == 0:
                    logger.error("⚠️  Empty audio chunk received!")
                    continue
                
                rms = audio.calculate_rms(chunk)
                current_time = time.time()
                elapsed = current_time - start_time
                
                rms_values.append(rms)
                timestamps.append(current_time - start_time)
                min_rms = min(min_rms, rms)
                max_rms = max(max_rms, rms)
                total_rms += rms
                sample_count += 1
                recent_values.append(rms)
                
                # Track baseline max during Phase 1
                if current_phase == 1:
                    baseline_max = max(baseline_max, rms)
                
                # Calculate recent average
                avg_rms = sum(recent_values) / len(recent_values) if recent_values else 0
                
                # Initialize dynamic_threshold for display
                dynamic_threshold = 0
                if current_phase == 1:
                    dynamic_threshold = baseline_max * 2.5  # Estimate for display
                
                # Phase transitions
                if current_phase == 1 and elapsed >= 10:
                    current_phase = 2
                    phase2_start = current_time
                    phase_start = current_time
                    baseline_avg = sum(rms_values) / len(rms_values) if rms_values else 0
                    
                    # Use microphone test max RMS as reference if available
                    mic_test_max = mic_test_max_rms
                    
                    # More sensitive threshold: use lower multiplier and consider mic test results
                    # If mic test showed higher RMS, use that as a better reference
                    reference_max = max(baseline_max, mic_test_max * 0.8) if mic_test_max > 0 else baseline_max
                    
                    # Calculate threshold: 1.3x reference or 2x average, but ensure it's reasonable
                    # Lower the multiplier from 2.5 to 1.3-1.5 for better sensitivity
                    preview_threshold = max(reference_max * 1.3, baseline_avg * 2, 30)
                    
                    # If mic test max was higher, we know claps can reach that level
                    # So threshold should be well below mic test max
                    if mic_test_max > 0:
                        preview_threshold = min(preview_threshold, mic_test_max * 0.7)
                    
                    dynamic_threshold = preview_threshold  # Initialize for Phase 2
                    print(f"\n✅ Baseline established! Average ambient RMS: {baseline_avg:.0f}")
                    print(f"   Maximum baseline RMS: {baseline_max:.0f}")
                    if mic_test_max > 0:
                        print(f"   Mic test peak RMS: {mic_test_max:.0f} (reference)")
                    print(f"🎯 Detection threshold: {preview_threshold:.0f}")
                    # Verify stream is still active before Phase 2
                    if not audio.is_stream_active():
                        logger.error("⚠️  Stream inactive before Phase 2! Restarting...")
                        if not audio.restart_stream():
                            logger.error("❌ Failed to restart stream. Exiting.")
                            break
                        logger.info("✅ Stream restarted for Phase 2")
                    
                    print(f"\n⏱️  Phase 2: Clap 5-10 times (will auto-end after {target_claps} claps or {phase2_max_duration}s)\n")
                    print("💡 TIP: Watch the RMS value - it should spike above the threshold when you clap!")
                    print(f"   └─ If your RMS values are below {preview_threshold:.0f}, clap louder or closer!")
                    print(f"   └─ Stream status: {'✅ Active' if audio.is_stream_active() else '❌ Inactive'}\n")
                
                # Real-time clap detection in Phase 2
                if current_phase == 2:
                    phase2_duration = current_time - phase2_start if phase2_start else 0
                    
                    # Debug: If RMS is suspiciously low during Phase 2, check audio data
                    if rms < 5 and phase2_duration < 5 and not low_rms_warned:
                        # First 5 seconds of Phase 2 with very low RMS - might indicate stream issue
                        chunk_max = np.abs(chunk).max() if len(chunk) > 0 else 0
                        if chunk_max < 100:  # Very small audio values
                            print(f"\n⚠️  WARNING: Audio seems very quiet (RMS: {rms:.0f}, Max: {chunk_max}).")
                            print(f"   Stream active: {audio.is_stream_active()}")
                            print(f"   └─ If RMS stays this low, your claps may not be detected!")
                            print(f"   └─ Try clapping louder or check microphone settings.\n")
                            low_rms_warned = True
                    
                    # More aggressive adaptive threshold - dynamically lower based on what we're seeing
                    # Track the highest RMS we've seen in Phase 2 so far
                    phase2_max_rms = max_rms  # This is the max from entire session, but will include Phase 2
                    
                    # If we see RMS significantly above baseline, lower threshold aggressively
                    if rms > baseline_max * 1.15:  # 15% above baseline
                        # We're seeing activity - calculate adaptive threshold
                        # Use 60% of highest RMS seen, or 1.15x baseline, whichever is more sensitive (lower)
                        adaptive_low = max(baseline_max * 1.15, 30)
                        adaptive_from_max = max(phase2_max_rms * 0.55, baseline_max * 1.1)  # 55% of max seen
                        dynamic_threshold = min(preview_threshold, adaptive_low, adaptive_from_max)
                        
                        # If current RMS is clearly above baseline but below threshold, lower threshold to catch it
                        if rms > baseline_max * 1.2 and rms < dynamic_threshold:
                            dynamic_threshold = max(rms * 0.7, baseline_max * 1.15, 30)
                    else:
                        dynamic_threshold = preview_threshold
                    
                    # Peak detection for real-time feedback
                    if len(recent_values) >= 5:
                        recent_list = list(recent_values)
                        # Calculate recent average EXCLUDING current value for better comparison
                        recent_avg = sum(recent_list[-7:-1]) / len(recent_list[-7:-1]) if len(recent_list) >= 7 else sum(recent_list[:-1]) / len(recent_list[:-1]) if len(recent_list) > 1 else 0
                        
                        # More sensitive detection: lower threshold multiplier for better detection
                        # Use dynamic_threshold which adapts, but also check against baseline
                        detection_threshold = dynamic_threshold
                        # If RMS is significantly above baseline, consider it a potential clap
                        baseline_multiplier = baseline_max * 1.1  # Very sensitive - 10% above baseline
                        detection_threshold = min(detection_threshold, max(baseline_multiplier, 3))  # Minimum 3
                        
                        # Simpler detection: RMS above threshold AND above baseline AND enough time passed
                        # Remove strict recent_avg requirement - if RMS is clearly above threshold, it's a clap
                        time_since_last = current_time - last_clap_detection
                        rms_above_threshold = rms > detection_threshold
                        rms_above_baseline = rms > baseline_max * 1.1
                        enough_time_passed = time_since_last > 0.3  # Reduced cooldown to 300ms
                        
                        if rms_above_threshold and rms_above_baseline and enough_time_passed:
                            # Check if it's a peak (local maximum) - more lenient check
                            is_peak = True
                            # Check only immediate neighbors, not wide window
                            window_size = 3
                            if len(recent_list) >= window_size:
                                # Check if current is higher than immediate neighbors
                                current_idx = -1
                                neighbors_checked = 0
                                for i in range(-window_size, 0):
                                    if i != current_idx and i < len(recent_list):
                                        if recent_list[i] >= rms:
                                            is_peak = False
                                            break
                                        neighbors_checked += 1
                                # If we don't have enough neighbors, still consider it a peak if above threshold
                                if neighbors_checked < 2:
                                    is_peak = True  # Be more lenient
                            else:
                                is_peak = True  # Not enough data, trust the threshold
                            
                            if is_peak:
                                detected_clap_count += 1
                                last_clap_detection = current_time
                                detected_claps_realtime.append((elapsed, rms))
                                print(f"\n   👏 Clap #{detected_clap_count} detected! (RMS: {rms:.0f}, Threshold: {detection_threshold:.0f})")
                                
                                # Auto-end Phase 2 if we detected enough claps
                                if detected_clap_count >= target_claps:
                                    print(f"\n✅ Detected {detected_clap_count} claps! Auto-ending Phase 2...")
                                    time.sleep(0.5)  # Brief pause to show final status
                                    break
                    
                    # Auto-end Phase 2 after max duration
                    if phase2_duration >= phase2_max_duration:
                        print(f"\n⏰ Phase 2 time limit reached ({phase2_max_duration}s). Proceeding to analysis...")
                        time.sleep(0.5)
                        break
                
                # Display current values with enhanced visibility
                phase_indicator = "🔇 Baseline" if current_phase == 1 else "👏 Clapping"
                time_remaining = ""
                if current_phase == 2 and phase2_start:
                    remaining = phase2_max_duration - phase2_duration
                    time_remaining = f" | ~{remaining:.0f}s left"
                
                # Enhanced RMS display for Phase 2
                if current_phase == 2:
                    # Show threshold and current RMS more prominently
                    threshold_display = f"Threshold: {dynamic_threshold:.0f}"
                    rms_status = "🔴" if rms < dynamic_threshold * 0.5 else "🟡" if rms < dynamic_threshold else "🟢"
                    status = f"{phase_indicator} | RMS: {rms:6.0f} {rms_status} | {threshold_display} | Max: {max_rms:.0f}"
                    status += f" | Claps: {detected_clap_count}/{target_claps}"
                    status += time_remaining
                    if rms > dynamic_threshold * 0.8:
                        status += " ⚠️  HIGH!"
                else:
                    status = f"{phase_indicator} | RMS: {rms:.0f} | Min: {min_rms:.0f} | Max: {max_rms:.0f} | Avg: {avg_rms:.0f}"
                
                print(f"\r{status}", end='', flush=True)
                
                time.sleep(0.05)  # Update every 50ms for smoother detection
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Calibration interrupted by user.")
            if current_phase == 2 and detected_clap_count > 0:
                print(f"   Detected {detected_clap_count} clap(s) before interruption. Analyzing collected data...\n")
            elif current_phase == 2:
                print(f"   Phase 2 was running. Analyzing collected data...\n")
        
        # Stop audio stream
        audio.stop_stream()
        print("\n\n" + "="*70)
        
        # Detailed Analysis
        elapsed = time.time() - start_time
        overall_avg = total_rms / sample_count if sample_count > 0 else 0
        
        if len(rms_values) < 20:
            logger.error("Calibration data too short. Please run again and collect at least 20 seconds of data.")
            return
        
        # Split data into baseline and clap phases
        baseline_samples = min(int(len(rms_values) * 0.3), int(10 / 0.05))  # First 10 seconds or 30%
        baseline_rms = rms_values[:baseline_samples] if baseline_samples > 0 else []
        clap_phase_rms = rms_values[baseline_samples:] if baseline_samples < len(rms_values) else rms_values
        
        # Calculate baseline statistics
        baseline_avg = sum(baseline_rms) / len(baseline_rms) if baseline_rms else overall_avg
        baseline_max = max(baseline_rms) if baseline_rms else 0
        baseline_std = 0
        if len(baseline_rms) > 1:
            variance = sum((x - baseline_avg) ** 2 for x in baseline_rms) / len(baseline_rms)
            baseline_std = variance ** 0.5
        
        # Use real-time detected claps if available, otherwise detect offline
        if detected_claps_realtime:
            # Use real-time detected claps (more reliable)
            claps = detected_claps_realtime
            print(f"✅ Using {len(claps)} claps detected in real-time during calibration")
        else:
            # Fallback to offline detection with adaptive threshold
            detection_threshold = max(baseline_avg + (baseline_std * 3), baseline_max * 2.0, 30)
            claps = detect_claps(clap_phase_rms, timestamps[baseline_samples:], detection_threshold)
            if not claps and max_rms > baseline_max * 1.5:
                # If offline detection failed but we see higher values, try lower threshold
                detection_threshold = max(baseline_max * 1.3, 20)
                claps = detect_claps(clap_phase_rms, timestamps[baseline_samples:], detection_threshold)
        
        # Calculate clap statistics
        clap_rms_values = [rms for _, rms in claps] if claps else []
        clap_avg = sum(clap_rms_values) / len(clap_rms_values) if clap_rms_values else 0
        clap_min = min(clap_rms_values) if clap_rms_values else 0
        clap_max = max(clap_rms_values) if clap_rms_values else 0
        
        # Calculate recommended thresholds
        # Conservative: 60% of average clap (reduces false positives)
        # Moderate: 50% of average clap (balanced)
        # Sensitive: 40% of average clap (catches quiet claps, may have false positives)
        
        if clap_avg > 0:
            threshold_conservative = int(clap_avg * 0.6)
            threshold_moderate = int(clap_avg * 0.5)
            threshold_sensitive = int(clap_avg * 0.4)
            
            # Ensure thresholds are above baseline + noise margin
            noise_margin = baseline_avg + (baseline_std * 2)
            threshold_conservative = max(threshold_conservative, int(noise_margin * 2))
            threshold_moderate = max(threshold_moderate, int(noise_margin * 1.5))
            threshold_sensitive = max(threshold_sensitive, int(noise_margin * 1.2))
        else:
            # Fallback if no claps detected - use max RMS from entire session
            # This helps if claps were quiet but still present
            session_max = max_rms
            if session_max > baseline_max * 1.2:
                # We see some activity above baseline
                threshold_conservative = int(session_max * 0.7)
                threshold_moderate = int(session_max * 0.6)
                threshold_sensitive = int(session_max * 0.5)
                logger.error(f"⚠️  No claps detected automatically, but detected peak RMS of {session_max:.0f}.")
                logger.error("   Using peak-based fallback calculation.")
                logger.error("   If claps aren't working, try clapping louder or closer to microphone.")
            else:
                # Very quiet session - conservative fallback
                threshold_conservative = int(baseline_max * 2.5)
                threshold_moderate = int(baseline_max * 2.0)
                threshold_sensitive = int(baseline_max * 1.5)
                logger.error("⚠️  No claps detected. Using baseline-based fallback.")
                logger.error("   Make sure you clapped loudly during Phase 2!")
        
        # Print detailed results
        print(" " * 15 + "📊 CALIBRATION ANALYSIS RESULTS")
        print("="*70)
        print(f"\n⏱️  Session Duration: {elapsed:.1f} seconds")
        print(f"📈 Total Samples: {sample_count}")
        print(f"👏 Claps Detected: {len(claps)}")
        
        print(f"\n{'─'*70}")
        print("🔇 AMBIENT NOISE BASELINE (Phase 1):")
        print(f"   Average RMS:    {baseline_avg:.0f}")
        print(f"   Maximum RMS:    {baseline_max:.0f}")
        print(f"   Std Deviation:  {baseline_std:.0f}")
        print(f"   Samples:        {len(baseline_rms)}")
        
        if claps:
            print(f"\n{'─'*70}")
            print("👏 CLAP ANALYSIS (Phase 2):")
            print(f"   Claps Detected: {len(claps)}")
            print(f"   Average Clap RMS: {clap_avg:.0f}")
            print(f"   Minimum Clap RMS: {clap_min:.0f}")
            print(f"   Maximum Clap RMS: {clap_max:.0f}")
            print(f"   Clap-to-Baseline Ratio: {clap_avg/baseline_avg:.1f}x" if baseline_avg > 0 else "   N/A")
            
            print(f"\n   Clap Peaks Detected:")
            for i, (t, rms) in enumerate(claps[:10], 1):  # Show first 10
                print(f"      #{i}: {t:.1f}s - RMS: {rms:.0f}")
            if len(claps) > 10:
                print(f"      ... and {len(claps) - 10} more")
        
        print(f"\n{'─'*70}")
        print("🎯 RECOMMENDED THRESHOLD VALUES:")
        print(f"\n   🟢 CONSERVATIVE: {threshold_conservative}")
        print(f"      └─ Best for: Quiet environments, avoiding false positives")
        print(f"      └─ Trade-off: May miss very quiet claps\n")
        
        print(f"   🟡 MODERATE:     {threshold_moderate} ⭐ RECOMMENDED")
        print(f"      └─ Best for: Balanced detection (default choice)")
        print(f"      └─ Trade-off: Good balance of detection vs false positives\n")
        
        print(f"   🟠 SENSITIVE:    {threshold_sensitive}")
        print(f"      └─ Best for: Noisy environments, catching all claps")
        print(f"      └─ Trade-off: May trigger on loud ambient sounds\n")
        
        print("="*70)
        print("\n📝 NEXT STEPS:")
        print(f"\n   1. Edit wakebot_config.json")
        print(f'   2. Change "threshold" to: {threshold_moderate}')
        print(f"   3. Save the file")
        print(f"   4. Test with: python main.py\n")
        
        if threshold_moderate < 500:
            print("⚠️  WARNING: Recommended threshold is quite low.")
            print("   If you experience false positives, try the CONSERVATIVE value instead.\n")
        elif threshold_moderate > 5000:
            print("⚠️  WARNING: Recommended threshold is quite high.")
            print("   Make sure you're clapping loud enough, or try the SENSITIVE value.\n")
        
        print("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"Calibration failed: {e}")
        import traceback
        traceback.print_exc()
        audio.stop_stream()


if __name__ == "__main__":
    main()
