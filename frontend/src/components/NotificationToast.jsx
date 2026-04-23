// filepath: frontend/src/components/NotificationToast.jsx
export default function NotificationToast({ notification }) {
  if (!notification || !notification.show) return null;

  const { hexUnlocked, hexAlreadyUnlocked, partnerName, reward, achievements, error, bank, message } = notification;

  return (
    <>
      <style>{`
        @keyframes slideDown {
          from { transform: translateY(-24px); opacity: 0; }
          to   { transform: translateY(0);     opacity: 1; }
        }
        .fow-toast { animation: slideDown 0.3s ease-out; }
      `}</style>
      <div
        className="fow-toast"
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 1000,
          pointerEvents: "none",
          padding: "12px 12px 0",
        }}
      >
        {bank ? (
          <BankPush bank={bank} />
        ) : (
          <div
            style={{
              background: "#0d0d1a",
              border: "1px solid #00C4FF",
              borderRadius: 14,
              padding: 14,
              maxWidth: 360,
              margin: "0 auto",
              color: "#00C4FF",
              boxShadow: "0 6px 24px rgba(0, 196, 255, 0.25)",
              pointerEvents: "auto",
            }}
          >
            {error && <div style={{ color: "#ff4d6d", fontSize: 14 }}>⚠ {error}</div>}

            {hexUnlocked && (
              <>
                <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6 }}>
                  🗺 Территория открыта!
                </div>
                {reward?.label && (
                  <div style={{ color: "#fff", fontSize: 14, marginBottom: 6 }}>
                    🎁 {reward.label}
                  </div>
                )}
              </>
            )}

            {!hexUnlocked && hexAlreadyUnlocked && reward?.label && (
              <>
                <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6 }}>
                  💳 Кэшбэк активирован{partnerName ? ` в ${partnerName}` : ""}
                </div>
                <div style={{ color: "#fff", fontSize: 14, marginBottom: 6 }}>
                  🎁 {reward.label}
                </div>
              </>
            )}

            {achievements && achievements.length > 0 && (
              <div style={{ marginTop: hexUnlocked ? 8 : 0 }}>
                {achievements.map((a) => (
                  <div key={a.code} style={{ fontSize: 13, color: "#ffd166", marginBottom: 4 }}>
                    <div>★ {a.name} — {a.reward_label}</div>
                    {a.reward?.code && (
                      <div style={{ fontFamily: "monospace", fontSize: 12, color: "#7B61FF", letterSpacing: 1 }}>
                        промокод: {a.reward.code}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {!hexUnlocked && !error && message && (
              <div style={{ fontSize: 13, color: "#ccc" }}>{message}</div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

function BankPush({ bank }) {
  return (
    <div
      style={{
        background: "#ffffff",
        borderRadius: 14,
        padding: "12px 14px",
        maxWidth: 380,
        margin: "0 auto",
        color: "#0d0d1a",
        boxShadow: "0 8px 28px rgba(0,0,0,0.35)",
        pointerEvents: "auto",
        display: "flex",
        gap: 12,
        alignItems: "flex-start",
      }}
    >
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: 8,
          background: "#E30613",
          color: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontWeight: 800,
          fontSize: 14,
          flex: "0 0 auto",
        }}
      >
        МТ
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#666", marginBottom: 2 }}>
          <span>МТБанк</span>
          <span>сейчас</span>
        </div>
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          Оплата · {bank.merchant}
        </div>
        <div style={{ fontSize: 13, color: "#333" }}>
          −{Number(bank.amount).toFixed(2)} BYN · карта *1234
        </div>
        <div style={{ fontSize: 12, color: "#E30613", marginTop: 4, fontWeight: 600 }}>
          {bank.hexAlreadyUnlocked
            ? `💳 Активируй кэшбэк${bank.cashbackPercent ? ` ${bank.cashbackPercent}%` : ""} в уведомлении`
            : "🔔 Новая территория на карте — открой её!"}
        </div>
      </div>
    </div>
  );
}
