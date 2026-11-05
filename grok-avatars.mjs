import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const [bundle, out] = process.argv.slice(2);
if (!bundle || !out) throw new Error("usage: node grok-avatars.mjs APP.ASAR OUT");
fs.mkdirSync(out, { recursive: true });
const fd = fs.openSync(bundle, "r");
const lead = Buffer.alloc(16);
fs.readSync(fd, lead, 0, lead.length, 0);
const header = Buffer.alloc(lead.readUInt32LE(12));
fs.readSync(fd, header, 0, header.length, 16);
let assets = JSON.parse(header.toString());
for (const key of ["dist", "electron-main", "menubar-tray", "assets"]) assets = assets.files[key];
for (const [shape, color] of [["cloud", "#bea5e0"], ["bean", "#f0c77d"], ["star", "#a9cfba"]]) {
	const name = `bot-${shape}@2x.png`;
	const entry = assets.files[name];
	if (!entry || entry.unpacked) throw new Error(`Missing packed avatar ${name}`);
	const png = Buffer.alloc(entry.size);
	fs.readSync(fd, png, 0, png.length, 8 + lead.readUInt32LE(4) + Number(entry.offset));
	const target = path.join(out, `${shape}.png`);
	fs.writeFileSync(target, png);
	execFileSync("magick", [target, "-fill", color, "-colorize", "100", target]);
}
fs.closeSync(fd);
const image = shape => `url("file://${path.resolve(out, `${shape}.png`)}")`;
fs.writeFileSync(path.join(out, "grok-avatars.css"), `
:root:not(#grok) [data-role='omp.bot.reply'] {
	position: relative;
	padding-left: 44px;
}
:root:not(#grok) [data-role='omp.bot.reply']::before {
	content: '';
	position: absolute;
	left: 0;
	top: 12px;
	width: 32px;
	height: 32px;
	background-image: ${image("cloud")};
	background-size: contain;
	background-repeat: no-repeat;
	animation: grok-avatar-bob 2.8s ease-in-out infinite alternate;
}
:root:not(#grok) :is([data-role='omp.bot.event.avatar'], [data-role='omp.bot.xavatar']) {
	width: 28px;
	height: 28px;
	background-image: ${image("bean")};
	background-size: contain;
	background-repeat: no-repeat;
	animation: grok-avatar-bob 3.2s ease-in-out infinite alternate;
}
:root:not(#grok) [data-role='omp.bot.xavatar'] {
	background-image: ${image("star")};
}
:root:not(#grok) :is([data-role='omp.bot.event.avatar'], [data-role='omp.bot.xavatar']) > * {
	display: none;
}
@keyframes grok-avatar-bob {
	from { transform: translateY(0); }
	to { transform: translateY(-2px); }
}
@media (prefers-reduced-motion: reduce) {
	:root:not(#grok) [data-role='omp.bot.reply']::before,
	:root:not(#grok) :is([data-role='omp.bot.event.avatar'], [data-role='omp.bot.xavatar']) {
		animation: none;
	}
}
`);
