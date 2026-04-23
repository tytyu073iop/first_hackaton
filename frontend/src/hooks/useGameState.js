// filepath: frontend/src/hooks/useGameState.js
import { useCallback, useEffect, useState } from "react";
import {
  consumePending,
  createPending,
  fetchHexes,
  fetchPartners,
  fetchPending,
  fetchProfile,
  fetchRewards,
  useReward,
} from "../api/client";

export function useGameState(playerId) {
  const [hexes, setHexes] = useState([]);
  const [partners, setPartners] = useState([]);
  const [pending, setPending] = useState([]);
  const [stats, setStats] = useState({ total: 0, unlocked: 0, achievements_count: 0 });
  const [achievements, setAchievements] = useState([]);
  const [rewards, setRewards] = useState({ active: [], used: [], expired: [] });
  const [notification, setNotification] = useState({ show: false });

  const refresh = useCallback(async () => {
    if (!playerId) return;
    try {
      const [hx, pr, pe, rw] = await Promise.all([
        fetchHexes(playerId),
        fetchProfile(playerId),
        fetchPending(playerId),
        fetchRewards(playerId),
      ]);
      setHexes(hx.hexes || []);
      setStats(hx.stats || { total: 0, unlocked: 0, achievements_count: 0 });
      setAchievements(pr.achievements || []);
      setPending(pe.pending || []);
      setRewards(rw || { active: [], used: [], expired: [] });
    } catch (e) {
      console.error("refresh failed", e);
    }
  }, [playerId]);

  const redeem = useCallback(async (rewardId) => {
    try {
      await useReward(rewardId);
      await refresh();
    } catch (e) {
      console.error("redeem failed", e);
    }
  }, [refresh]);

  useEffect(() => {
    refresh();
    fetchPartners()
      .then((d) => setPartners(d.partners || []))
      .catch((e) => console.error("partners failed", e));
  }, [refresh]);

  useEffect(() => {
    if (!playerId) return;
    const id = setInterval(() => {
      fetchPending(playerId)
        .then((d) => {
          const arr = d.pending || [];
          setPending((prev) => {
            const prevIds = new Set(prev.map((x) => x.pending_id));
            const fresh = arr.filter((x) => !prevIds.has(x.pending_id));
            if (fresh.length > 0) {
              const f = fresh[0];
              setNotification({
                show: true,
                bank: {
                  merchant: f.partner_name,
                  amount: f.amount,
                  mcc: f.category,
                  hexAlreadyUnlocked: f.hex_already_unlocked,
                  cashbackPercent: f.cashback_percent,
                },
              });
              setTimeout(() => setNotification({ show: false }), 4500);
            }
            return arr;
          });
        })
        .catch(() => {});
    }, 5000);
    return () => clearInterval(id);
  }, [playerId]);

  useEffect(() => {
    if (!playerId) return;
    const id = setInterval(() => {
      fetchHexes(playerId)
        .then((hx) => {
          setHexes(hx.hexes || []);
          setStats(hx.stats || { total: 0, unlocked: 0, achievements_count: 0 });
        })
        .catch(() => {});
    }, 10000);
    return () => clearInterval(id);
  }, [playerId]);

  const submitDeferred = useCallback(
    async (merchantName, amount, mcc, partnerId) => {
      if (!playerId) return;
      try {
        await createPending(playerId, merchantName, amount, mcc, partnerId);
        setNotification({
          show: true,
          bank: { merchant: merchantName, amount, mcc },
        });
        setTimeout(() => setNotification({ show: false }), 4500);
        setTimeout(() => refresh(), 400);
      } catch (e) {
        console.error("submitDeferred failed", e);
        setNotification({ show: true, error: "Ошибка сети" });
        setTimeout(() => setNotification({ show: false }), 2500);
      }
    },
    [playerId, refresh]
  );

  const consume = useCallback(
    async (pendingId) => {
      try {
        const res = await consumePending(pendingId);
        if (res.hex_unlocked) {
          setHexes((prev) =>
            prev.map((h) =>
              h.hex_id === res.hex_unlocked
                ? { ...h, is_unlocked: true, _justUnlocked: true }
                : h
            )
          );
        }
        setNotification({
          show: true,
          hexUnlocked: res.hex_unlocked,
          hexAlreadyUnlocked: res.hex_already_unlocked,
          partnerName: res.partner?.name,
          reward: res.reward,
          achievements: res.new_achievements || [],
        });
        setTimeout(() => setNotification({ show: false }), 4000);
        setTimeout(() => refresh(), 400);
      } catch (e) {
        console.error("consume failed", e);
        setNotification({ show: true, error: "Ошибка сети" });
        setTimeout(() => setNotification({ show: false }), 2500);
      }
    },
    [refresh]
  );

  return { hexes, partners, pending, stats, achievements, rewards, notification, submitDeferred, consume, redeem };
}
