import { useState } from "react";
import { askQuestion, uploadPDF } from "./api";

export default function App() {
  const [file, setFile] = useState(null);
  const [upload, setUpload] = useState(null);
  const [message, setMessage] = useState("");
  const [answer, setAnswer] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  const busy =
    status === "uploading" || status === "asking";

  const uploadDisabled = !file || busy;

  const askDisabled =
    !upload || !message.trim() || busy;

  function handleFileChange(event) {
    const selectedFile = event.target.files?.[0] || null;

    setFile(selectedFile);
    setUpload(null);
    setAnswer(null);
    setError("");
  }

  async function handleUpload(event) {
    event.preventDefault();

    if (!file || busy) {
      return;
    }

    setUpload(null);
    setAnswer(null);
    setError("");
    setStatus("uploading");

    try {
      const result = await uploadPDF(file);
      setUpload(result);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "The PDF could not be uploaded.",
      );
    } finally {
      setStatus("idle");
    }
  }

  async function handleQuestion(event) {
    event.preventDefault();

    const trimmedMessage = message.trim();

    if (!upload || !trimmedMessage || busy) {
      return;
    }

    setAnswer(null);
    setError("");
    setStatus("asking");

    try {
      const result = await askQuestion(trimmedMessage);
      setAnswer(result);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "The question could not be answered.",
      );
    } finally {
      setStatus("idle");
    }
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <p className="eyebrow">AI Coding Workshop · Day 2</p>
        <h1>SmartLearn Lite</h1>
        <p>
          Upload a text-based PDF, ask a question, and
          verify the answer using its cited pages.
        </p>
      </header>

      <section
        className="panel"
        aria-labelledby="upload-heading"
      >
        <div className="step-heading">
          <span>1</span>
          <div>
            <h2 id="upload-heading">
              Select and upload
            </h2>
            <p>
              PDFs may contain at most 30 pages and must
              include selectable text.
            </p>
          </div>
        </div>

        <form onSubmit={handleUpload}>
          <label htmlFor="pdf-file">
            PDF document
          </label>

          <input
            id="pdf-file"
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            disabled={busy}
          />

          {file && (
            <p className="selected-file">
              Selected: {file.name}
            </p>
          )}

          <button
            type="submit"
            disabled={uploadDisabled}
          >
            {status === "uploading"
              ? "Uploading..."
              : "Upload PDF"}
          </button>
        </form>

        {upload && (
          <div className="receipt" aria-live="polite">
            <strong>Upload complete</strong>
            <dl>
              <div>
                <dt>File</dt>
                <dd>{upload.filename}</dd>
              </div>
              <div>
                <dt>Pages</dt>
                <dd>{upload.pages}</dd>
              </div>
              <div>
                <dt>Characters</dt>
                <dd>{upload.characters}</dd>
              </div>
            </dl>
          </div>
        )}
      </section>

      <section
        className="panel"
        aria-labelledby="question-heading"
      >
        <div className="step-heading">
          <span>2</span>
          <div>
            <h2 id="question-heading">
              Ask and verify
            </h2>
            <p>
              Questions become available after a successful
              upload.
            </p>
          </div>
        </div>

        <form onSubmit={handleQuestion}>
          <label htmlFor="question">
            Question
          </label>

          <textarea
            id="question"
            value={message}
            onChange={(event) =>
              setMessage(event.target.value)
            }
            placeholder="Which frameworks are used on Day 2?"
            rows="4"
            disabled={!upload || busy}
          />

          <button
            type="submit"
            disabled={askDisabled}
          >
            {status === "asking"
              ? "Asking..."
              : "Ask question"}
          </button>
        </form>

        {answer && (
          <article
            className="answer"
            aria-live="polite"
          >
            <h3>Answer</h3>
            <p>{answer.answer}</p>

            {answer.citations?.length > 0 && (
              <div className="citations">
                <strong>Source pages</strong>
                <div className="citation-list">
                  {answer.citations.map((page) => (
                    <span
                      className="page-chip"
                      key={page}
                    >
                      Page {page}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </article>
        )}
      </section>

      {error && (
        <div className="error-message" role="alert">
          <strong>Something went wrong.</strong>
          <span>{error}</span>
        </div>
      )}
    </main>
  );
}