# Generative-AI usage log (IAG level 3 — collaboration)

| # | Date | Tool | Team member | Prompt | Input | Result |
|---|------|------|-------------|--------|-------|--------|
| 1 | 2026-09-28 | Claude | Maria Alejandra Enriquez | "Requiero entender que debo hacer para esta tarea integradora" | Assignment PDF | Explanation of the stages and deliverables |
| 2 | 2026-09-28 | Claude | Maria Camila Cordoba | "No entendí lo de los perfiles propios" | — | Explanation of team-defined profiles |
| 3 | 2026-09-28 | Claude | Maria Alejandra Enriquez | "¿Cómo debemos nombrar el repo?" | — | Repository naming suggestions |
| 4 | 2026-09-28 | Claude | Maria Alejandra Enriquez | "Dame opciones para elegir los dos perfiles que faltan" | — | Options; team chose DevOps Engineer + Data Analyst |
| 5 | 2026-09-28 | Claude | Maria Camila Cordoba | "Entonces esta opción DevOps Engineer + Data Analyst, ahora qué sigue para hacer con los ejemplos" | Profile choice | Work plan |
| 6 | 2026-09-28 | Claude | Maria Alejandra Enriquez | "Ayudanos con la interfaz porfa, como empezamos, queriamos irnos por la opcion de pagina web" | — | First version of the interface |
| 7 | 2026-09-28 | Claude | Maria Camila Cordoba | "Me puedes ayudar con inos test? no puedo identificar porque no esta dando estos" |
| 8 | 2026-09-28 | Claude | Maria Camila Cordoba | "Crees que nuestra integradora esta cumpliendo con la rubrica? Queremos ver si nos saltamos algo" | — | Review of the integrative task |
| 9 | 2026-09-29 | Claude | Maria Alejandra Enriquez | "Q nos conviene más para la página web Streamlit, Flask o Tkinter? No sabemos nada de frontend" | — | Comparison of options, team chose Streamlit |
| 10 | 2026-09-29 | Claude | Maria Camila Cordoba | "¿Cómo organizamos app.py? Queremos una parte para analizar la hoja de vida y otra para validar un .resume" | pipeline.py | Two-tab layout (st.tabs) with wide page config |
| 11 | 2026-09-30 | Claude | Maria Alejandra Enriquez | "Queremos que el usuario pueda escoger un ejemplo de samples, subir un .txt o escribirlo a mano, ¿cómo se hace?" | — | Selectbox + file uploader + text area, team added errors="replace" |
| 12 | 2026-09-30 | Claude | Maria Camila Cordoba | "Cuando cambio de ejemplo en el selectbox el texto no cambia, se queda el anterior" | Screenshot of the app | Explanation of widget state; fixed with key=f"text_{choice}" |
| 13 | 2026-10-01 | Claude | Maria Alejandra Enriquez | "¿Cómo mostramos las 4 etapas en orden para la sustentación? Que se vea qué sale de cada una" | AnalysisResult | One subheader per stage with tables, warnings and code blocks |
| 14 | 2026-10-01 | Claude | Maria Camila Cordoba | "En la etapa 3 queremos ver rápido qué perfiles aceptó cada autómata y qué le faltó a los que rechazó" | ProfileResult | Automaton type, sequence (ε if empty) and missing requirements |
| 15 | 2026-10-02 | Claude | Maria Alejandra Enriquez | "El HTML del candidato daña los estilos de Streamlit cuando lo mostramos, y queremos poder descargarlo" | app.py | Switched to components.html (iframe); added download buttons for .html and .resume |
| 16 | 2026-10-02 | Claude | Maria Camila Cordoba | "En la pestaña de validar queremos que diga si el error es sintáctico o semántico y en qué línea" | dsl/__init__.py | try/except per error type showing line and column; tested with samples/invalid/ |
| 17 | 2026-10-03 | Claude | Maria Alejandra Enriquez | "La app se demora cada vez que tocamos algo, pq?" | — | Explanation of Streamlit reruns; added @st.cache_resource |
| 18 | 2026-10-05 | Claude | Maria Camila Cordoba | "Queremos que el HTML se vea como una hoja de vida y que dibuje el camino del autómata con círculos y flechas, sin JavaScript" | render.py | CSS design idea; team implemented _path_html with double circle for final state |
| 19 | 2026-10-05 | Claude | Maria Alejandra Enriquez | "El profe dijo que el HTML debe salir de la especificación validada, ¿cómo cambiamos render.py?" | Assignment PDF | to_html now reads only the textX model |
| 20 | 2026-10-06 | Claude | Maria Camila Cordoba | "¿Se puede probar la interfaz con pytest sin abrir el navegador?" | app.py | Explanation of AppTest; team wrote tests/test_ui.py |
| 21 | 2026-10-07 | Claude | Maria Alejandra Enriquez | "Nos sale que streamlit no se reconoce como comando en la terminal de VS Code" | Error message | Virtual environment steps for Windows; added to README |
| 22 | 2026-10-08 | Claude | Maria Camila Cordoba | "¿Cómo hacemos un transductor en pyformlang para que JS y Javascript den JAVASCRIPT?" | — | Small FST example; team defined variants in catalog.py |
| 23 | 2026-10-09 | Claude | Maria Alejandra Enriquez | "Dnde validamos en textX que una habilidad no esté en la categoría equivocada?" | resume.tx | Explanation of object processors (semantic checks) |
| 24 | 2026-10-12 | Claude | Maria Camila Cordoba | "¿Qué casos de prueba nos faltan? Solo la lista, sin código" | docs/test_cases.md | Suggested cases: empty sequence, duplicated skills, unrecognized skills |