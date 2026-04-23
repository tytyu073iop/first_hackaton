// filepath: frontend/src/components/DemoPanel.jsx
import { useEffect, useRef, useState } from "react";

const inputStyle = {
  background: "#0d0d1a",
  color: "#fff",
  border: "1px solid #1f3a52",
  borderRadius: 10,
  padding: "12px 12px",
  fontSize: 15,
  fontFamily: "inherit",
  outline: "none",
  width: "100%",
  boxSizing: "border-box",
  minHeight: 44,
};

const btnStyle = {
  background: "#FFD60A",
  color: "#0d0d1a",
  border: "none",
  borderRadius: 10,
  padding: "12px 18px",
  fontSize: 15,
  fontWeight: 700,
  cursor: "pointer",
  fontFamily: "inherit",
  width: "100%",
  minHeight: 48,
};

export default function DemoPanel({
  stats,
  achievements,
  rewards,
  onRedeem,
  submitDeferred,
  partners,
  pendingCount,
  player,
  onLogout,
  selectedPartner,
}) {
  const [partnerId, setPartnerId] = useState("");
  const [amount, setAmount] = useState("25");
  const [rewardsOpen, setRewardsOpen] = useState(false);
  const [rewardsTab, setRewardsTab] = useState("active");
  const [redeemedFlash, setRedeemedFlash] = useState(null);
  const amountRef = useRef(null);
  const activeRewards = rewards?.active ?? [];
  const usedRewards = rewards?.used ?? [];
  const expiredRewards = rewards?.expired ?? [];
  const inactiveRewards = [...usedRewards, ...expiredRewards];

  function handleRedeem(r) {
    if (!onRedeem) return;
    onRedeem(r.id);
    const labelByType = {
      cashback_boost: `+${r.value}% кэшбэк${r.scope ? " · " + r.scope : ""} активен`,
      discount: `Скидка ${r.value}% активна`,
      bonus_points: `+${r.value} бонусов начислено`,
      free_unlock: "Бесплатное открытие активно",
    };
    setRedeemedFlash({
      id: r.id,
      text: labelByType[r.reward_type] || "Промокод активирован",
    });
    setTimeout(() => {
      setRedeemedFlash((cur) => (cur && cur.id === r.id ? null : cur));
    }, 3000);
  }

  useEffect(() => {
    if (selectedPartner?.id != null && String(selectedPartner.id) !== partnerId) {
      setPartnerId(String(selectedPartner.id));
      setTimeout(() => amountRef.current?.focus(), 50);
    }
  }, [selectedPartner]); // eslint-disable-line react-hooks/exhaustive-deps

  const partner = partners?.find((p) => String(p.id) === partnerId);

  function handlePay(e) {
    e.preventDefault();
    if (!partner) return;
    const amt = Number(amount);
    if (!amt || amt <= 0) return;
    submitDeferred(partner.name, amt, partner.mcc_code, partner.id);
  }

  return (
    <div
      style={{
        background: "#0d0d1a",
        borderTop: "1px solid #00C4FF",
        padding: 12,
        color: "#00C4FF",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 10,
          fontSize: 12,
          color: "#888",
          gap: 8,
          flexWrap: "wrap",
        }}
      >
        <span style={{ minWidth: 0, overflow: "hidden", textOverflow: "ellipsis" }}>
          {player && (
            <>
              <b style={{ color: "#00C4FF" }}>{player.name}</b> · код:{" "}
              <span style={{ color: "#fff", letterSpacing: 1 }}>{player.recovery_code}</span>
            </>
          )}
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {pendingCount > 0 && (
            <span
              style={{
                background: "#FFD60A",
                color: "#0d0d1a",
                padding: "3px 10px",
                borderRadius: 12,
                fontSize: 12,
                fontWeight: 700,
              }}
              title="Банк прислал транзакции — открой их на карте"
            >
              🔔 {pendingCount}
            </span>
          )}
          {(activeRewards.length > 0 || inactiveRewards.length > 0 || rewardsOpen) && (
            <button
              onClick={() => setRewardsOpen((v) => !v)}
              style={{
                background: "#7B61FF",
                color: "#fff",
                border: "none",
                padding: "3px 10px",
                borderRadius: 12,
                fontSize: 12,
                fontWeight: 700,
                cursor: "pointer",
                fontFamily: "inherit",
              }}
              title="Активные промокоды"
            >
              🎁 {activeRewards.length}
            </button>
          )}
          <span>{stats?.unlocked ?? 0}/{stats?.total ?? 0}</span>
          {onLogout && (
            <button
              onClick={onLogout}
              style={{
                background: "transparent",
                color: "#888",
                border: "none",
                cursor: "pointer",
                fontSize: 12,
                fontFamily: "inherit",
                padding: "6px 4px",
              }}
            >
              выйти
            </button>
          )}
        </span>
      </div>

      {achievements && achievements.length > 0 && (
        <div style={{ marginBottom: 10, display: "flex", gap: 6, flexWrap: "wrap" }}>
          {achievements.map((a) => (
            <span
              key={a.code}
              title={`${a.name}${a.description ? " — " + a.description : ""}`}
              style={{
                background: "#1a1a2e",
                border: "1px solid #00C4FF",
                borderRadius: 12,
                padding: "3px 10px",
                fontSize: 12,
                color: "#00C4FF",
              }}
            >
              ★ {a.name}
            </span>
          ))}
        </div>
      )}

      <form
        onSubmit={handlePay}
        style={{ display: "flex", gap: 8, flexDirection: "column" }}
      >
        <select
          value={partnerId}
          onChange={(e) => setPartnerId(e.target.value)}
          style={inputStyle}
          required
        >
          <option value="">— Выбери партнёра —</option>
          {partners?.map((p) => (
            <option key={p.id} value={String(p.id)}>
              {p.name} · {p.cashback_percent}%
            </option>
          ))}
        </select>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            ref={amountRef}
            type="number"
            min="1"
            step="1"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            style={{ ...inputStyle, flex: "0 0 120px" }}
            placeholder="BYN"
            required
          />
          <button type="submit" style={btnStyle} disabled={!partner}>
            Оплатить
          </button>
        </div>
      </form>

      <div style={{ fontSize: 11, color: "#666", marginTop: 8, textAlign: "center" }}>
        После оплаты банк пришлёт уведомление — открой территорию на карте
      </div>

      {rewardsOpen && (
        <div
          style={{
            marginTop: 10,
            background: "#111125",
            border: "1px solid #7B61FF",
            borderRadius: 10,
            padding: 10,
            maxHeight: 260,
            overflowY: "auto",
          }}
        >
          <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
            {[
              { key: "active", label: `Активные (${activeRewards.length})` },
              { key: "inactive", label: `Неактивные (${inactiveRewards.length})` },
            ].map((t) => {
              const selected = rewardsTab === t.key;
              return (
                <button
                  key={t.key}
                  onClick={() => setRewardsTab(t.key)}
                  style={{
                    flex: 1,
                    background: selected ? "#7B61FF" : "transparent",
                    color: selected ? "#fff" : "#aaa",
                    border: "1px solid #7B61FF",
                    borderRadius: 8,
                    padding: "6px 8px",
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: "pointer",
                    fontFamily: "inherit",
                  }}
                >
                  {t.label}
                </button>
              );
            })}
          </div>

          {rewardsTab === "active" && (
            <>
              {activeRewards.length === 0 && (
                <div style={{ fontSize: 12, color: "#666" }}>Пусто</div>
              )}
              {activeRewards.map((r) => {
                const expDays = Math.max(
                  0,
                  Math.ceil((new Date(r.expires_at) - new Date()) / 86400000)
                );
                return (
                  <div
                    key={r.id}
                    style={{
                      borderBottom: "1px solid #1f1f33",
                      padding: "8px 0",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontWeight: 600, color: "#fff", fontSize: 13 }}>
                        {r.title}
                      </div>
                      <div
                        style={{
                          fontFamily: "monospace",
                          fontSize: 12,
                          color: "#7B61FF",
                          letterSpacing: 1,
                        }}
                      >
                        {r.code}
                      </div>
                      <div style={{ fontSize: 11, color: "#666" }}>
                        осталось {expDays} дн.
                      </div>
                    </div>
                    {redeemedFlash && redeemedFlash.id === r.id ? (
                      <span
                        style={{
                          color: "#7CFFB2",
                          fontSize: 12,
                          fontWeight: 600,
                          whiteSpace: "nowrap",
                        }}
                      >
                        ✓ {redeemedFlash.text}
                      </span>
                    ) : (
                      <button
                        onClick={() => handleRedeem(r)}
                        style={{
                          background: "transparent",
                          color: "#7B61FF",
                          border: "1px solid #7B61FF",
                          borderRadius: 6,
                          padding: "4px 10px",
                          fontSize: 12,
                          cursor: "pointer",
                          fontFamily: "inherit",
                        }}
                      >
                        использовать
                      </button>
                    )}
                  </div>
                );
              })}
            </>
          )}

          {rewardsTab === "inactive" && (
            <>
              {inactiveRewards.length === 0 && (
                <div style={{ fontSize: 12, color: "#666" }}>Пусто</div>
              )}
              {inactiveRewards.map((r) => {
                const isUsed = !!r.used_at;
                const statusText = isUsed
                  ? `использован ${new Date(r.used_at).toLocaleDateString()}`
                  : `истёк ${new Date(r.expires_at).toLocaleDateString()}`;
                const statusColor = isUsed ? "#7CFFB2" : "#E07A5F";
                return (
                  <div
                    key={r.id}
                    style={{
                      borderBottom: "1px solid #1f1f33",
                      padding: "8px 0",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: 8,
                      opacity: 0.7,
                    }}
                  >
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div
                        style={{
                          fontWeight: 600,
                          color: "#ccc",
                          fontSize: 13,
                          textDecoration: "line-through",
                        }}
                      >
                        {r.title}
                      </div>
                      <div
                        style={{
                          fontFamily: "monospace",
                          fontSize: 12,
                          color: "#666",
                          letterSpacing: 1,
                        }}
                      >
                        {r.code}
                      </div>
                    </div>
                    <span
                      style={{
                        color: statusColor,
                        fontSize: 11,
                        fontWeight: 600,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {isUsed ? "✓" : "⌛"} {statusText}
                    </span>
                  </div>
                );
              })}
            </>
          )}
        </div>
      )}
    </div>
  );
}
