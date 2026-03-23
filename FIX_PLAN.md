# VoicePipe - Root Cause Analysis & Fix Plan

## Root Cause Analysis

### Issue 1: Installer Can't Build whisper.cpp
**Root Cause:** Using `make whisper-cli` instead of CMake
```bash
# Wrong:
make whisper-cli

# Correct:
cmake -B build
cmake --build build -j --config Release
```

### Issue 2: Agent Has No Microphone
**Root Cause:** listen() returns None always - no audio input implementation
```python
# Current (broken):
async def listen(self) -> Optional[bytes]:
    return None  # Does nothing!

# Need: pyaudio, sounddevice, or browser-based input
```

### Issue 3: CLI TTS File Saving Crashes
**Root Cause:** Wrong WAV handling - writing to wave.Wave_write object instead of file
```python
# Wrong:
f.write(audio[44:])  # Writing to wrong object

# Correct: Write properly
```

### Issue 4: Async Is Fake
**Root Cause:** Just wrapping sync in executor, no real async
- This is actually OK for CPU-bound tasks
- But needs better implementation for streaming

### Issue 5: All Tools Are Placeholders
**Root Cause:** No actual implementation
- weather → needs API
- search → needs search API
- open_app → needs platform-specific code

---

## Fix Plan

### Phase 1: Fix Installer
- [x] Use CMake instead of Make
- [x] Add pre-built binary download fallback
- [x] Add better error messages

### Phase 2: Fix CLI
- [x] Fix WAV writing
- [ ] Add proper audio format handling

### Phase 3: Fix Agent
- [ ] Add microphone input (sounddevice/pyaudio)
- [ ] Add audio playback
- [ ] Implement real tools

### Phase 4: Polish
- [ ] Add tests
- [ ] Add type hints
- [ ] Remove bare excepts
- [ ] Add input validation