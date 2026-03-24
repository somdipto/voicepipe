# VOICEPIPE v0.6.0 - DEEP ROAST REPORT

## 🔥 CRITICAL FLAWS (FIX NOW)

### 1. eval() Security Hole - CRITICAL 🔴
```python
# agent.py:278
result = eval(expr)  # DANGER! User input can execute ANY code
```
**Impact:** Anyone can execute `rm -rf /` or steal data
**Fix:** Use `ast.literal_eval()` or a safe parser

### 2. Hardcoded Paths - CRITICAL 🔴
```python
# installer.py:56, 116, 211, 228
Path("/root/whisper.cpp/build/bin/whisper-cli")  # Only works on THIS machine
```
**Impact:** Won't work on user's machine
**Fix:** Use `which` or cache_dir relative paths

### 3. No Microphone on Fresh Install - CRITICAL 🔴
```python
# agent.py - sounddevice requires PortAudio
import sounddevice as sd  # Raises OSError if no PortAudio
```
**Impact:** Agent can't listen at all
**Fix:** Add browser-based audio input (WebRTC)

---

## 🟠 HIGH PRIORITY ISSUES

### 4. Fake Async - HIGH
```python
# agent.py - all "async def" just wrap sync code
async def respond(self, text: str) -> str:  # No actual async
    return await asyncio.to_thread(self._respond_sync, text)
```
**Impact:** No concurrency benefit
**Fix:** Actually use async or remove async keyword

### 5. No Input Sanitization - HIGH
```python
# agent.py:276 - calculate tool
expression = re.findall(r'[\d\.\+\-\*\/\(\)]+', text)
result = eval(expr)  # Still dangerous even with regex
```
**Impact:** Code injection possible
**Fix:** Use safe math parser

### 6. Global State in __init__.py - HIGH
```python
# __init__.py:8
voice = VoicePipeline()  # Created at import time!
```
**Impact:** Side effects at import, hard to test
**Fix:** Lazy initialization

### 7. No Version Pinning - HIGH
```python
# pyproject.toml
dependencies = ["numpy>=1.20.0"]  # Too loose!
```
**Impact:** Breaking changes from any version
**Fix:** Pin exact versions: `numpy==1.26.0`

---

## 🟡 MEDIUM ISSUES

### 8. Empty pass in Exception Classes
```python
# tts.py:21, stt.py:21
class TTSError(Exception):
    pass  # No docstring, no custom behavior
```
**Impact:** Missed opportunity for useful error info

### 9. No Type Hints on Some Functions
```python
# voice_pipeline.py
def check_status(self):  # Should be -> dict
```
**Impact:** Harder to maintain

### 10. No Logging Configuration
```python
# All files
logger = logging.getLogger("voicepipe")  # No config
```
**Impact:** No control over log levels
**Fix:** Add logging.basicConfig() in __init__

### 11. No CI/CD Pipeline
- No GitHub Actions
- No automated tests on push
- No linting

---

## 🟢 MINOR/NITPICKS

### 12. Inconsistent Error Messages
- Some raise `TTSError`, some raise generic `Exception`
- No error code standardization

### 13. No README for Each Module
- Agent tools not documented
- Installation not beginner-friendly

### 14. Missing __all__ Exports
```python
# __init__.py - no __all__ defined
```

### 15. Audio.py is Almost Empty
- Only 4587 bytes
- Could be merged or removed

---

## 📊 STATS

| Metric | Count |
|--------|-------|
| Total Lines | 1923 |
| Python Files | 8 |
| Critical Issues | 3 |
| High Priority | 4 |
| Medium | 3 |
| Minor | 5 |

---

## 🎯 FIX PRIORITY

1. **FIX NOW:** eval() security hole
2. **FIX NOW:** Hardcoded paths
3. **Next:** Add real microphone (browser audio)
4. **Next:** Version pinning
5. **Next:** Remove global state
6. **Later:** Add CI/CD

---

*Roast complete. Want me to fix these?*
