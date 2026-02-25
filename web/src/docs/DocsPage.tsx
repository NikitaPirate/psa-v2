import { useMemo, useState } from "react";
import { parseCanonicalStrategy, stringifyCanonicalStrategy } from "../lib/strategy";
import {
  CONTEXT_FOR_HUMAN_VERBATIM,
  DOCS_JSON_EXAMPLE,
  DOCS_TEXT,
  DocsLocale,
} from "./content";
import { docsPromptByLocale } from "./prompt";

export type { DocsLocale } from "./content";

type DocsPageProps = {
  locale: DocsLocale;
  onNavigateToApp: (mode: "create" | "use") => void;
  onLocaleChange: (locale: DocsLocale) => void;
};

function copyWithExecCommand(value: string): boolean {
  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  textarea.style.pointerEvents = "none";
  document.body.append(textarea);
  textarea.select();
  textarea.setSelectionRange(0, textarea.value.length);
  const copied = document.execCommand("copy");
  textarea.remove();
  return copied;
}

async function copyText(value: string): Promise<boolean> {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(value);
      return true;
    } catch {
      return copyWithExecCommand(value);
    }
  }

  return copyWithExecCommand(value);
}

export function DocsPage({ locale, onNavigateToApp, onLocaleChange }: DocsPageProps) {
  const t = DOCS_TEXT;
  const prompt = useMemo(() => docsPromptByLocale(locale), [locale]);
  const jsonExample = useMemo(() => stringifyCanonicalStrategy(DOCS_JSON_EXAMPLE), []);
  const [copyStatus, setCopyStatus] = useState<string>("");

  const copyPrompt = async () => {
    const copied = await copyText(prompt);
    setCopyStatus(copied ? t.promptCopied[locale] : t.promptCopyError[locale]);
  };

  parseCanonicalStrategy(jsonExample);

  return (
    <main className="app-shell docs-shell">
      <header className="panel docs-header">
        <h1>{t.title[locale]}</h1>
        <div className="docs-header-actions">
          <div className="mode-toggle" role="navigation" aria-label="App sections">
            <button type="button" onClick={() => onNavigateToApp("create")}>
              {t.createTab[locale]}
            </button>
            <button type="button" onClick={() => onNavigateToApp("use")}>
              {t.useTab[locale]}
            </button>
            <button type="button" className="active" aria-current="page">
              {t.docsTab[locale]}
            </button>
          </div>

          <div className="docs-language" role="group" aria-label={t.language[locale]}>
            <button
              type="button"
              className={locale === "en" ? "active" : ""}
              onClick={() => onLocaleChange("en")}
            >
              EN
            </button>
            <button
              type="button"
              className={locale === "ru" ? "active" : ""}
              onClick={() => onLocaleChange("ru")}
            >
              RU
            </button>
          </div>
        </div>
      </header>

      <section className="panel docs-toc">
        <h2>{t.tocTitle[locale]}</h2>
        <ul>
          <li>
            <a href="#context-for-human">{t.contextTitle[locale]}</a>
          </li>
          <li>
            <a href="#prompt-for-ai">{t.promptTitle[locale]}</a>
          </li>
          <li>
            <a href="#how-to-read-charts">{t.chartsTitle[locale]}</a>
          </li>
          <li>
            <a href="#configure-strategy">{t.configureTitle[locale]}</a>
          </li>
          <li>
            <a href="#json-workflow">{t.jsonTitle[locale]}</a>
          </li>
        </ul>
      </section>

      <section id="context-for-human" className="panel docs-panel">
        <h2>{t.contextTitle[locale]}</h2>
        <p>{CONTEXT_FOR_HUMAN_VERBATIM.intro[locale]}</p>
        <p>{CONTEXT_FOR_HUMAN_VERBATIM.assumptionsLabel[locale]}</p>
        <ul>
          {CONTEXT_FOR_HUMAN_VERBATIM.assumptions[locale].map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <p>{CONTEXT_FOR_HUMAN_VERBATIM.disclaimer[locale]}</p>
        <p>{CONTEXT_FOR_HUMAN_VERBATIM.strategyDefinition[locale]}</p>
        <p>{CONTEXT_FOR_HUMAN_VERBATIM.configurableLabel[locale]}</p>
        <ul>
          {CONTEXT_FOR_HUMAN_VERBATIM.configurableItems[locale].map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <p>{CONTEXT_FOR_HUMAN_VERBATIM.outputPolicy[locale]}</p>
      </section>

      <section id="prompt-for-ai" className="panel docs-panel">
        <h2>{t.promptTitle[locale]}</h2>
        <div className="docs-inline-copy">
          <p>{t.promptLine[locale]}</p>
          <button type="button" onClick={() => void copyPrompt()}>
            {t.copyPrompt[locale]}
          </button>
        </div>
        {copyStatus ? <p className="status">{copyStatus}</p> : null}
      </section>

      <section id="how-to-read-charts" className="panel docs-panel">
        <h2>{t.chartsTitle[locale]}</h2>
        <ul>
          {t.chartsItems[locale].map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section id="configure-strategy" className="panel docs-panel">
        <h2>{t.configureTitle[locale]}</h2>
        <p>{t.configureIntro[locale]}</p>
        <ul>
          {t.configureItems[locale].map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section id="json-workflow" className="panel docs-panel">
        <h2>{t.jsonTitle[locale]}</h2>
        <p>{t.jsonIntro[locale]}</p>

        <h3>{t.jsonConstraintsTitle[locale]}</h3>
        <ul>
          {t.jsonConstraints[locale].map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>

        <pre className="docs-json-block" aria-label="Canonical strategy JSON example">
          <code>{jsonExample}</code>
        </pre>

        <h3>{t.jsonTransferTitle[locale]}</h3>
        <ul>
          {t.jsonTransferItems[locale].map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
