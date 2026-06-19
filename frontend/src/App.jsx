import { useEffect, useRef, useState } from "react";
import { fetchProducts, fetchRecommendations } from "./api.js";

const EXAMPLES = [
  "I want a phone under $500",
  "Best laptop for video editing, budget isn't a big issue",
  "Cheap earbuds for the gym",
  "Something for taking notes on the go",
];

export default function App() {
  const [products, setProducts] = useState([]);
  const [productsError, setProductsError] = useState("");

  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("idle");
  const [note, setNote] = useState("");
  const [picks, setPicks] = useState({});
  const [pickOrder, setPickOrder] = useState([]);
  const [errorMsg, setErrorMsg] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch((err) => setProductsError(err.message));
  }, []);

  const runQuery = async (overrideQuery) => {
    const trimmed = (overrideQuery ?? query).trim();
    if (!trimmed) return;
    setStatus("loading");
    setErrorMsg("");
    try {
      const result = await fetchRecommendations(trimmed);
      const pickMap = {};
      const order = [];
      (result.picks || []).forEach((p) => {
        pickMap[p.id] = p.reason;
        order.push(p.id);
      });
      setPicks(pickMap);
      setPickOrder(order);
      setNote(result.note || "");
      setStatus("done");
    } catch (err) {
      setStatus("error");
      setErrorMsg(err.message || "Something went wrong talking to the AI.");
    }
  };

  const handleExample = (text) => {
    setQuery(text);
    runQuery(text);
  };

  const handleClear = () => {
    setPicks({});
    setPickOrder([]);
    setNote("");
    setStatus("idle");
    setErrorMsg("");
    setQuery("");
    inputRef.current && inputRef.current.focus();
  };

  const hasPicks = pickOrder.length > 0;

  const sortedProducts = hasPicks
    ? [
        ...pickOrder.map((id) => products.find((p) => p.id === id)).filter(Boolean),
        ...products.filter((p) => !picks[p.id]),
      ]
    : products;

  return (
    <div className="shell">
      <div className="masthead">
        <h1>Catalog</h1>
        <span className="count mono">{products.length} products</span>
      </div>

      <div className="ask-panel">
        <p className="ask-label">Ask the AI for a recommendation</p>
        <div className="ask-row">
          <input
            ref={inputRef}
            type="text"
            placeholder='e.g. "I want a phone under $500"'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") runQuery();
            }}
          />
          <button onClick={() => runQuery()} disabled={status === "loading" || !query.trim()}>
            {status === "loading" ? "Thinking…" : "Recommend"}
          </button>
        </div>

        <div className="examples">
          {EXAMPLES.map((ex) => (
            <button key={ex} className="example-chip" onClick={() => handleExample(ex)}>
              {ex}
            </button>
          ))}
        </div>

        {status === "loading" && (
          <p className="ai-note loading">Asking the AI to match products against your request…</p>
        )}

        {status === "error" && (
          <p className="ai-note error">
            <span className="tag">error</span>
            {errorMsg}
          </p>
        )}

        {status === "done" && (
          <p className="ai-note">
            <span className="tag">ai</span>
            {note || (hasPicks ? "Here's what fits best." : "No catalog match for that request.")}
            <button className="clear-link" onClick={handleClear}>
              clear
            </button>
          </p>
        )}
      </div>

      {productsError && (
        <p className="ai-note error" style={{ marginBottom: "16px" }}>
          <span className="tag">error</span>
          Could not load products: {productsError}.
        </p>
      )}

      <div className="grid">
        {sortedProducts.map((p) => {
          const isPick = !!picks[p.id];
          const pickIndex = isPick ? pickOrder.indexOf(p.id) + 1 : null;
          return (
            <div key={p.id} className={"product" + (isPick ? " recommended" : "")}>
              {isPick && (
                <div className="pick-badge">
                  <span className="num">{pickIndex}</span>
                  <span className="why">{picks[p.id]}</span>
                </div>
              )}
              <div>
                <p className="p-name">{p.name}</p>
                <p className="p-meta mono">{p.meta}</p>
              </div>
              <span className="p-price">${p.price}</span>
              <span className="p-cat">{p.category}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
