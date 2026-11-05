import { readFileSync } from "node:fs";
import { AssistantMessageComponent } from "@oh-my-pi/pi-tui/chat/assistant-message";
import { UserMessageComponent } from "@oh-my-pi/pi-tui/chat/user-message";
import { AskDialogComponent } from "@oh-my-pi/pi-tui/overlays/ask-dialog";
import { Composer } from "@oh-my-pi/pi-tui/prompt/composer";
import { col, row, text } from "@oh-my-pi/pi-tui/native/describe";
import { TranscriptContainer } from "@oh-my-pi/pi-tui/chrome";

const CUE = "/run/user/1001/agent/ozette-opus/yorha/v3/cue";
const wrap = native => ({ render: () => [], invalidate() {}, describe: () => native });
const tok = s => Math.max(1, Math.round(s.length / 4));

const USER1 = "Could you check the smaller memory limits before we change the default?";
const REPLY1 = "## A little room to breathe\n\nThe **768 MiB** ceiling keeps the build comfortable. At `512 MiB`, linking is too close to the edge.\n\n```sh\nnix build .#tern --no-link\n```\n\nI would keep the smaller limit for quick checks, and leave the full build some headroom.";
const USER2 = "Where does the link step actually peak? I'd rather not guess.";
const REPLY2 = "## Where the link step peaks\n\nOnly the final link of `stencil_tern` goes past **600 MiB**; everything before it stays near 300.\n\n- codegen units: **212 MiB** each, four at a time\n- final `lld` link: **611 MiB** for about nine seconds\n- with LTO off the link drops to **430 MiB**\n\n```sh\n/usr/bin/time -v nix build .#tern --no-link 2>&1 | grep Maximum\n```\n\nSo 768 MiB leaves roughly 150 MiB of headroom at the peak, and 512 MiB only holds with LTO off.";
const WORDS2 = REPLY2.split(/(?<=\s)/);

function tags(kind, cells, live) {
  return row(cells.map((c, i) => text(c, { role: i === 0 ? "oz.tag.n" : "oz.tag", wrap: "none" })), { role: `oz.tags.${kind}${live ? ".live" : ""}`, gap: "none" });
}

export default function trailsScene(pi) {
  if (process.env.OMP_BOT_NAME !== "Kino") return;
  pi.on("session_start", async (_event, ctx) => {
    if (ctx.agent?.kind === "sub" || ctx.mode !== "tui") return;
    ctx.ui.setWidget("omp-bot-floor", undefined, { placement: "belowEditor" });
    ctx.ui.setWidget("ozette-trails", tui => {
      const state = TranscriptContainer.prototype[Symbol.for("omp-bot.transcript")].state;
      state.bot.hero = false;
      state.bot.name = "Kino";
      state.bot.line = "Ready when you are.";
      state.bot.stopTimers();
      state.bot.nap = () => {};
      const head = state.top;
      const status = state.status;
      const stamp = wrap(text("Today 15:14", { role: "omp.bot.time" }));
      const event = wrap(col([row([text("Message from", { role: "omp.bot.event.action" }), text("Mori", { role: "omp.bot.event.name" }), text("›", { role: "omp.bot.event.more" })], { role: "omp.bot.event.row", gap: "xs", align: "center" })], { role: "omp.bot.eventbox.purple" }));
      const you = (msg, cells) => {
        const c = new UserMessageComponent(msg);
        return { render: () => [], invalidate() {}, describe: cx => col([tags("you", cells), c.describe(cx)], { role: "omp.bot.you" }) };
      };
      const reply = (md, cells, live, stop) => {
        const c = new AssistantMessageComponent({ role: "assistant", content: [{ type: "text", text: md }], stopReason: (stop ?? !live) ? "stop" : undefined, timestamp: Date.now() }, true);
        return { render: () => [], invalidate() {}, describe: cx => col([tags("bot", cells, live), c.describe(cx)], { role: "omp.bot.reply" }) };
      };
      const ask = new AskDialogComponent([{ id: "ceiling", header: "Kino asks", question: "Which ceiling should become the default?", options: [{ label: "768 MiB", description: "Comfortable build headroom" }, { label: "512 MiB", description: "Tight limit, LTO off" }, { label: "Keep 2 GiB", description: "Leave the default alone" }] }], { onSubmit: () => {}, onCancel: () => {} }, { tui });
      try { ask.handleInput("\x1b[B"); } catch {}

      const u1 = you(USER1, ["01", `${tok(USER1)} tok`, "15:14"]);
      const r1 = reply(REPLY1, ["02", `${tok(REPLY1)} tok`, "2.1 s"]);
      const u2 = you(USER2, ["03", `${tok(USER2)} tok`, "15:16"]);
      const base = [head, stamp, u1, event, r1];
      let main = [...base, status];
      let dock = [];
      let timers = [];
      const clear = () => { for (const t of timers) clearTimeout(t); timers = []; };
      const r2c = new AssistantMessageComponent(undefined, true);
      let r2cells = ["04", "0 tok", "0.0 s"];
      let r2live = true;
      const r2 = { render: () => [], invalidate() {}, describe: cx => col([tags("bot", r2cells, r2live), r2c.describe(cx)], { role: "omp.bot.reply" }) };
      const streamAt = (n, liveOverride) => {
        const md = WORDS2.slice(0, n).join("");
        const done = n >= WORDS2.length;
        r2live = liveOverride ?? !done;
        r2c.updateContent({ role: "assistant", content: [{ type: "text", text: md }], stopReason: r2live ? undefined : "stop", timestamp: 1 }, { transient: r2live });
        if (!r2live) r2c.markTranscriptBlockFinalized();
        r2cells = ["04", `${tok(md)} tok`, `${(n * 0.045 + 0.3).toFixed(1)} s`];
        return r2;
      };
      const set = (m, d) => { main = m; dock = d; tui.requestRender(); };
      const full = () => streamAt(WORDS2.length);
      const uAns = you("512 MiB, and keep LTO off for the link.", ["05", "9 tok", "15:18"]);
      const apply = cue => {
        const kind = cue.split(":")[0];
        if (kind === "down") { try { ask.handleInput("\x1b[B"); } catch {} return tui.requestRender(); }
        if (kind === "up") { try { ask.handleInput("\x1b[A"); } catch {} return tui.requestRender(); }
        if (kind === "type") {
          const ed = globalThis.__yhComposer?.editor;
          const s = "Where does the link step actually peak?";
          let t = 0;
          for (let i = 0; i < s.length; i += 2) { const ch = s.slice(i, i + 2); timers.push(setTimeout(() => { try { ed.insertText(ch); } catch {} tui.requestRender(); }, t)); t += 45; }
          return;
        }
        if (kind === "clear") { try { globalThis.__yhComposer?.editor.setText(""); } catch {} return tui.requestRender(); }
        clear();
        if (kind === "base") return set([...base, status], []);
        if (kind === "sent") { try { globalThis.__yhComposer?.editor.setText(""); } catch {} return set([...base, u2], []); }
        if (kind === "final") return set([...base, u2, full(), status], [ask]);
        if (kind === "done") return set([...base, u2, full(), status], []);
        if (kind === "ask") return set([...base, u2, full(), status], [ask]);
        if (kind === "submit") return set([...base, u2, full(), uAns], []);
        if (kind === "dismiss") return set([...base, u2, full(), status], []);
        if (kind === "stream") {
          set([...base, u2], []);
          let t = 300;
          for (let n = 12; n <= WORDS2.length; n += 3) {
            const k = n;
            timers.push(setTimeout(() => set([...base, u2, streamAt(k)], []), t));
            t += 50;
          }
          t += 300;
          timers.push(setTimeout(() => set([...base, u2, full(), status], []), t));
          return;
        }
        if (kind === "go") {
          set([...base, status], []);
          let t = 600;
          timers.push(setTimeout(() => set([...base, u2], []), t));
          t += 900;
          for (let n = 12; n <= WORDS2.length; n++) {
            const k = n;
            timers.push(setTimeout(() => set([...base, u2, streamAt(k)], []), t));
            t += 55;
          }
          t += 500;
          timers.push(setTimeout(() => set([...base, u2, full(), status], []), t));
          t += 900;
          timers.push(setTimeout(() => set([...base, u2, full(), status], [ask]), t));
        }
      };
      let last = "";
      setInterval(() => {
        let cue = "base";
        try { cue = readFileSync(CUE, "utf8").trim() || "base"; } catch {}
        if (cue !== last) { last = cue; apply(cue); }
      }, 40);

      const proto = Composer.prototype;
      const original = proto.describeSurface;
      proto.describeSurface = function (cx) {
        globalThis.__yhComposer = this;
        const surface = original.call(this, cx);
        return { ...surface, main, dock: [...dock, ...surface.dock] };
      };
      tui.requestRender();
      return wrap(col([]));
    });
  });
}
