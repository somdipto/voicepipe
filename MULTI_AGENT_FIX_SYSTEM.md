# VoicePipe Multi-Agent Fix System

## Architecture: Ralph Loop + GSD + BMAD

```
┌─────────────────────────────────────────────────────────────────┐
│                    LEAD ARCHITECT AGENT                          │
│  (Coordinates all agents, ensures GSD - Get Shit Done)      │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ FIXER AGENT  │     │ TEST AGENT  │     │ DOCS AGENT  │
│ (Implements) │     │ (Verifies)  │     │ (Documents)  │
└──────────────┘     └──────────────┘     └──────────────┘
                              │
                              ▼
                 ┌──────────────────────┐
                 │ VERIFICATION LOOP   │
                 │ (BMAD - Build More  │
                 │      And Deploy)    │
                 └──────────────────────┘
```

## Agent Prompts

### Lead Architect
"You are the lead architect. Coordinate the fix of VoicePipe. Use GSD methodology: Get Shit Done. Create a todo list, prioritize issues, assign to agents, verify results. Start now."

### Fixer Agent
"You are a senior fixer agent. Fix the following issues in VoicePipe:
1. Remove all bare except: statements
2. Fix sounddevice PortAudio dependency
3. Add input validation
4. Fix STT auto-download
5. Add real agent tools
Use BMAD: Build More And Deploy - complete each fix and verify."

### Test Agent  
"You are QA agent. Test VoicePipe fixes:
1. Run all commands
2. Verify TTS works
3. Verify CLI works
4. Check for errors
Report results."

### Docs Agent
"You are documentation agent. Update VoicePipe docs:
1. Update README with real usage
2. Fix installation instructions
3. Document all features
Be accurate."

---

## Execution Plan

### Phase 1: Setup Multi-Agent System
- [x] Design architecture
- [ ] Create agent prompts

### Phase 2: Execute Fixes (GSD)
- [ ] Agent 1: Remove bare excepts
- [ ] Agent 2: Fix dependencies
- [ ] Agent 3: Add validation
- [ ] Agent 4: Fix STT

### Phase 3: Verify (BMAD)
- [ ] Test all features
- [ ] Fix what breaks
- [ ] Deploy

---

## Commands

```bash
# Start fixing process
python -m agents.fix_all

# Run verification
python -m agents.verify
```