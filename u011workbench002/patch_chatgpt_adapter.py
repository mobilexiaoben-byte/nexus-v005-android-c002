from pathlib import Path
import sys

path = Path(sys.argv[1])
s = path.read_text(encoding="utf-8")
s = s.replace("const CHANNEL='NEXUS_POC022_C8B2R1';", "const CHANNEL='NEXUS_U011_CHATGPT_WORKBENCH_V1';")
s = s.replace("NEXUS C8B2R1 — ", "NEXUS U011 WORKBENCH — ")
s = s.replace("nexus-c8b2r1-chatgpt-badge", "nexus-u011-workbench-chatgpt-badge")
s = s.replace("[NEXUS C8B2R1] real ChatGPT UI provider bridge active", "[NEXUS U011 WORKBENCH] ChatGPT analysis provider bridge active")

start = s.find("  function buildPrompt(envelope){")
end = s.find("  async function progress", start)
if start < 0 or end < 0:
    raise SystemExit("CHATGPT_BUILD_PROMPT_BLOCK_NOT_FOUND")

newfun = """  function buildPrompt(envelope){
    const frozen=envelope.frozen_package||{};
    const pack=JSON.stringify(frozen,null,2);
    const resultVersion=String(frozen?.output_contract?.result_pack_version||'U011_WORKBENCH_RESULT_V1');
    const comparisonId=String(frozen?.output_contract?.comparison_id||'');
    const analysisId=String(frozen.analysis_id||'');
    const subjectId=String(frozen.subject_id||'');
    return [
      'You are executing a NEXUS read-only analysis in this authenticated ChatGPT browser session.',
      '',
      'MANDATORY EXECUTION RULES:',
      '- Answer the user question analytically and directly.',
      '- You may use your internal model knowledge, but do NOT browse the web, call tools, or perform external research.',
      '- Treat previous_context as context, not as automatically verified fact.',
      '- Preserve uncertainty and distinguish fact, inference, and hypothesis when relevant.',
      '- Do NOT canonicalize anything and do NOT mutate any NEXUS state.',
      '- Do NOT declare a truth winner.',
      '- Return exactly ONE JSON object and nothing else.',
      '- The answer field must contain the substantive analysis in prose.',
      '- For model.provider use exactly \"OpenAI\".',
      '- For model.model use exactly \"ChatGPT UI session — exact backend model not exposed by bridge\".',
      '',
      'RETURN THIS JSON SHAPE WITH THE CORRELATION VALUES EXACTLY AS GIVEN:',
      JSON.stringify({
        result_pack_version:resultVersion,
        pack_id:String(frozen.pack_id||''),
        comparison_id:comparisonId,
        analysis_id:analysisId,
        subject_id:subjectId,
        model:{
          provider:'OpenAI',
          model:'ChatGPT UI session — exact backend model not exposed by bridge'
        },
        answer:'<your substantive analysis here>',
        audit:{
          external_research:false,
          canonical_write:false,
          state_mutation_mode:'NONE',
          truth_winner:'NONE'
        }
      },null,2),
      '',
      'QUESTION:',
      String(envelope.question||''),
      '',
      'FROZEN NEXUS CONTEXT:',
      pack,
      '',
      'Generate the completed Result Pack now.'
    ].join('\\n');
  }

"""
s = s[:start] + newfun + s[end:]
path.write_text(s, encoding="utf-8")
