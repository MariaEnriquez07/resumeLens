"""ResumeLens graphical interface.

    streamlit run app.py

Shows the output of every stage so the formal models can be followed step by
step (useful for the demo and the presentation).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from resumelens import dsl
from resumelens.pipeline import ResumeLens

SAMPLES = Path(__file__).parent / "samples"


@st.cache_resource
def get_lens() -> ResumeLens:
    return ResumeLens()


st.set_page_config(page_title="ResumeLens", layout="wide")
st.title("ResumeLens")
st.caption("Checks whether the qualifications written in a résumé satisfy formally "
           "defined profile patterns. It does not rank candidates or make hiring decisions.")

tab_analyze, tab_validate = st.tabs(["Analyze a résumé", "Validate a profile specification"])

with tab_analyze:
    samples = sorted(p.name for p in SAMPLES.glob("*.txt"))
    choice = st.selectbox("Load a sample résumé", ["(write my own)"] + samples)
    default = "" if choice == "(write my own)" else (SAMPLES / choice).read_text(encoding="utf-8")
    uploaded = st.file_uploader("…or upload a .txt résumé", type=["txt"])
    if uploaded is not None:
        default = uploaded.read().decode("utf-8", errors="replace")
    text = st.text_area("Résumé text", value=default, height=220, key=f"text_{choice}")

    if st.button("Run pipeline", type="primary", disabled=not text.strip()):
        result = get_lens().analyze(text)

        st.subheader("Stage 1 · Extraction (regular expressions)")
        ex = result.extraction
        c1, c2 = st.columns(2)
        c1.write({"name": ex.name, "emails": ex.emails, "phones": ex.phones,
                  "linkedin": ex.linkedin, "github": ex.github,
                  "experience_years": ex.experience_years})
        c2.dataframe([{"category": s.category, "text as written": s.text,
                       "span": f"{s.start}–{s.end}"} for s in ex.skills],
                     use_container_width=True)

        st.subheader("Stage 2 · Normalization (finite-state transducers)")
        st.dataframe([{"raw": r, "canonical": c, "transducer": t}
                      for r, c, t in result.normalization.mapping],
                     use_container_width=True)
        if result.normalization.unrecognized:
            st.warning("Not recognised by any transducer: "
                       + ", ".join(result.normalization.unrecognized))

        st.subheader("Stage 3 · Pattern recognition (finite automata)")
        for r in result.classification:
            icon = "✅" if r.accepted else "❌"
            with st.expander(f"{icon} {r.title} — {r.status} ({r.automaton_kind})",
                             expanded=r.accepted):
                st.code(" ".join(r.sequence) or "ε (empty sequence)")
                if r.missing:
                    st.write("Missing requirements: " + "; ".join(r.missing))

        st.subheader("Stage 4 · Candidate profile language (textX)")
        st.code(result.dsl_text, language="text")
        st.success("The specification was validated by the grammar.")
        components.html(result.html, height=700, scrolling=True)
        st.download_button("Download HTML", result.html, file_name="candidate.html")
        st.download_button("Download specification (.resume)", result.dsl_text,
                           file_name="candidate.resume")

with tab_validate:
    spec = st.text_area("Paste a .resume specification", height=300,
                        value=(SAMPLES / "valid_minimal.resume").read_text(encoding="utf-8"))
    if st.button("Validate"):
        try:
            model = dsl.parse(spec)
        except dsl.TextXSyntaxError as e:
            st.error(f"Rejected — lexical/syntax error at {e.line}:{e.col}: {e.message}")
        except dsl.TextXSemanticError as e:
            st.error(f"Rejected — semantic error at {e.line}:{e.col}: {e.message}")
        else:
            from resumelens.render import to_html
            st.success(f"Valid profile for {model.candidate.name}")
            components.html(to_html(model), height=600, scrolling=True)