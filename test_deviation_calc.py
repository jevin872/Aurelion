"""
Quick test to calculate deviation with new lenient scaling.
"""

# Your values
phase_baseline = 0.7626
phase_test = 0.5691
spectral_baseline = 1530.57
spectral_test = 1132.27

# Feature weights
weights = {
    'mfcc': 0.45,
    'phase': 0.30,
    'spectral': 0.25,
    'jitter': 0.00
}

# Phase deviation (new lenient scaling)
phase_diff = abs(phase_test - phase_baseline)
phase_deviation = min(1, phase_diff / 1.0)  # Was 0.5, now 1.0

print(f"Phase Calculation:")
print(f"  Baseline: {phase_baseline:.4f}")
print(f"  Test:     {phase_test:.4f}")
print(f"  Diff:     {phase_diff:.4f}")
print(f"  Deviation: {phase_deviation:.3f} (was {min(1, phase_diff / 0.5):.3f})")
print()

# Spectral deviation (new lenient scaling)
spectral_diff_percent = abs(spectral_test - spectral_baseline) / spectral_baseline
spectral_deviation = min(1, spectral_diff_percent / 0.60)  # Was 0.40, now 0.60

print(f"Spectral Calculation:")
print(f"  Baseline: {spectral_baseline:.2f}")
print(f"  Test:     {spectral_test:.2f}")
print(f"  Diff:     {spectral_diff_percent:.1%}")
print(f"  Deviation: {spectral_deviation:.3f} (was {min(1, spectral_diff_percent / 0.40):.3f})")
print()

# Assume MFCC is good (let's say 0.05 deviation)
mfcc_deviation = 0.05

# Weighted deviation
weighted_deviation = (
    mfcc_deviation * weights['mfcc'] +
    phase_deviation * weights['phase'] +
    spectral_deviation * weights['spectral']
)

old_weighted_deviation = (
    mfcc_deviation * weights['mfcc'] +
    min(1, phase_diff / 0.5) * weights['phase'] +
    min(1, spectral_diff_percent / 0.40) * weights['spectral']
)

print(f"Weighted Deviation:")
print(f"  MFCC:     {mfcc_deviation:.3f} × {weights['mfcc']:.0%} = {mfcc_deviation * weights['mfcc']:.3f}")
print(f"  Phase:    {phase_deviation:.3f} × {weights['phase']:.0%} = {phase_deviation * weights['phase']:.3f}")
print(f"  Spectral: {spectral_deviation:.3f} × {weights['spectral']:.0%} = {spectral_deviation * weights['spectral']:.3f}")
print(f"  Total:    {weighted_deviation:.3f} ({weighted_deviation:.1%})")
print(f"  Old Total: {old_weighted_deviation:.3f} ({old_weighted_deviation:.1%})")
print()

# Threshold check
threshold = 0.45  # Normal threshold
print(f"Threshold Check (Normal = {threshold:.0%}):")
print(f"  New Deviation: {weighted_deviation:.1%} < {threshold:.0%}? {weighted_deviation < threshold}")
print(f"  Old Deviation: {old_weighted_deviation:.1%} < {threshold:.0%}? {old_weighted_deviation < threshold}")
print()

if weighted_deviation < threshold:
    print("✅ MATCH - Voice matches signature!")
else:
    print("❌ MISMATCH - Voice does not match signature")
