#!/usr/bin/env node
/*
dashboard_tjek.js — proev dashboard.html i en rigtig browser (audit 2026-11-13).

Testsuiten er ren Python og ser ikke dashboardet. Auditten 2026-11-13 fandt fire fejl i siden, som kun en browser
viser, og dette script holder dem ude:
  1. Hovedbogsgrafens maanedsetiketter stoedte sammen fra 7 raekker paa en telefon (februar-laesningen 2027) og fra
     13 paa en bred skaerm. Tidsaksen har nu to lag (maanedsnavne og aarstal), der tyndes ud efter pladsen.
  2. En fejl under tegningen (fx et manglende felt i dashboard.json) efterlod en halv side uden besked.
  3. Translitterationen aendrede filnavne og hashes ("BEDØMMELSESNØGLE.md", "6bæade4"), flertals-oe ("datør") og
     afsnitsnumre ("diagnostik 4,5").
  4. Hovedbogstabellen viste ikke raekkens note, kalibrering, input og P paa maanedstal.

Koer:    node v5/dashboard_tjek.js [--hurtig]
         --hurtig proever et udsnit af raekkeantallene (ca. et halvt minut i stedet for nogle minutter).
Kraever: Node og Playwright med Chromium (npm install playwright && npx playwright install chromium).
         Ikke en del af CI. Koer det, naar dashboard.html aendres.

Scriptet serverer repo-roden lokalt, tegner siden med den committede dashboard.json og med syntetiske varianter af
den (1-480 maaneders hovedbog, huller, 2027-raekker, manglende felter), og maaler i browseren. Eksterne kald
(webfontene) afbrydes, saa der bruges browserens egen monospace; den har samme tegnbredde som sidens skrift.
Skriver intet i repoet. Exit 1 ved fejl.

Kendt graense, ikke en fejl: over ca. 90 maaneder paa en telefon er kolonnerne smallere end en synlig prik, saa
prikkerne roerer hinanden. Etiketterne stoeder stadig ikke sammen.
*/
"use strict";
const { chromium } = require("playwright");
const fs = require("fs"), http = require("http"), os = require("os"), path = require("path");

const ROD = path.resolve(__dirname, "..");
const HURTIG = process.argv.includes("--hurtig");
const base = JSON.parse(fs.readFileSync(path.join(ROD, "dashboard.json"), "utf8"));
const tilstand = { json: base, status: 200, indlejret: null };
const TOM_INDLEJRING = '<script id="indlejret" type="application/json"></script>';

const srv = http.createServer((req, res) => {
  const u = req.url.split("?")[0];
  if (u === "/dashboard.json") {
    if (tilstand.status !== 200) { res.statusCode = tilstand.status; return res.end("nej"); }
    res.setHeader("content-type", "application/json");
    return res.end(typeof tilstand.json === "string" ? tilstand.json : JSON.stringify(tilstand.json));
  }
  if (u === "/dashboard.html") {
    let h = fs.readFileSync(path.join(ROD, "dashboard.html"), "utf8");
    if (tilstand.indlejret !== null) h = h.replace(TOM_INDLEJRING, TOM_INDLEJRING.replace("><", ">" + tilstand.indlejret + "<"));
    res.setHeader("content-type", "text/html; charset=utf-8");
    return res.end(h);
  }
  res.statusCode = 404; res.end("nej");
});

// ---------- syntetiske hovedboeger
const kopi = o => JSON.parse(JSON.stringify(o));
const sidste = base.hovedbog[base.hovedbog.length - 1];
const ym = t => `${Math.floor(t / 12)}-${String(t % 12 + 1).padStart(2, "0")}`;
const hul = m => ({ logget: `${m} (ikke logget)`, snapshot: "–", P: "ikke logget", baand: "", basisrate: "", dom: "", kurve: "",
  antaending: "", note: "ingen raekke i logvinduet", kalibrering: "", vindue: "", input: "", P_maanedlig: "",
  p_tal: null, baand_tal: null, basisrate_tal: null, kurve_tal: null, p_maanedlig_tal: null });
function hovedbog(n, start, huller) {                    // n maaneder fra start = [aar, maaned]; huller = positioner uden laesning
  const d = kopi(base); d.hovedbog = [];
  for (let k = 0; k < n; k++) {
    const m = ym(start[0] * 12 + start[1] - 1 + k);
    if (huller && huller.has(k)) { d.hovedbog.push(hul(m)); continue; }
    const p = 0.10 + 0.012 * ((k * 7) % 10);
    d.hovedbog.push(Object.assign({}, sidste, { logget: m + "-10", snapshot: m + "-10", p_tal: p, baand_tal: [p - 0.05, p + 0.08], basisrate_tal: 0.18 }));
  }
  return d;
}

// ---------- maaling i browseren: al tekst i hovedbogsgrafen
function maalGraf() {
  const svg = document.querySelector('svg[aria-label^="Hovedbogens"]');
  if (!svg) return null;
  const R = e => { const r = e.getBoundingClientRect(); return { l: r.left, r: r.right, t: r.top, b: r.bottom, s: e.textContent }; };
  const ov = (a, b) => a.l < b.r - 0.6 && b.l < a.r - 0.6 && a.t < b.b - 0.6 && b.t < a.b - 0.6;
  const ramme = svg.getBoundingClientRect();
  const tekst = [...svg.querySelectorAll("text")].map(R);
  const akse = [...svg.querySelectorAll(".tidsakse text")].map(e => e.textContent);
  const prikker = [...svg.querySelectorAll("circle")].map(R).sort((a, b) => a.l - b.l);
  const streger = [...svg.querySelectorAll("line.basislinje")].map(R).sort((a, b) => a.l - b.l);
  const maerker = [...svg.querySelectorAll("circle, rect")].map(R);
  const fund = [];
  for (let i = 0; i < tekst.length; i++) for (let j = i + 1; j < tekst.length; j++)
    if (ov(tekst[i], tekst[j])) fund.push(`tekst overlapper: "${tekst[i].s}" og "${tekst[j].s}"`);
  for (const t of tekst) if (t.l < ramme.left - 0.6 || t.r > ramme.right + 0.6 || t.t < ramme.top - 0.6 || t.b > ramme.bottom + 0.6) fund.push(`tekst uden for grafen: "${t.s}"`);
  for (const h of tekst.filter(t => t.s === "ikke logget")) if (maerker.some(m => ov(h, m))) fund.push('"ikke logget" ligger oven paa en raekke');
  if (!akse.some(s => /^\d{4}$/.test(s))) fund.push("intet aarstal paa tidsaksen");
  let prik = 0, streg = 0;
  for (let i = 1; i < prikker.length; i++) if (prikker[i].l < prikker[i - 1].r - 0.3) prik++;
  for (let i = 1; i < streger.length; i++) if (streger[i].l < streger[i - 1].r - 0.3) streg++;
  if (document.documentElement.scrollWidth > document.documentElement.clientWidth) fund.push("siden ruller vandret");
  return { fund: [...new Set(fund)], prik, streg, maaneder: akse.filter(s => /^[a-z]{3}$/.test(s)), aar: akse.filter(s => /^\d{4}$/.test(s)) };
}

const fejl = [];
const F = (hvor, hvad) => fejl.push(`${hvor}: ${hvad}`);
const MND = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"];

(async () => {
  await new Promise(r => srv.listen(0, "127.0.0.1", r));
  const URL = `http://127.0.0.1:${srv.address().port}/dashboard.html`;
  const browser = await chromium.launch();
  async function aabn(bredde, skema) {
    const ctx = await browser.newContext({ viewport: { width: bredde, height: 900 }, colorScheme: skema || "light" });
    await ctx.route(u => !u.href.startsWith("http://127.0.0.1"), r => r.abort());        // ingen eksterne kald (webfonte)
    const side = await ctx.newPage(); const sidefejl = [];
    side.on("pageerror", e => sidefejl.push(e.message));
    const hent = async () => {                           // en side, der aldrig bliver klar, er et fund, ikke et nedbrud af tjekket
      try {
        await side.goto(URL);
        await side.waitForFunction(() => document.querySelector("h1") || (document.getElementById("vaelg") && !document.getElementById("vaelg").hidden), null, { timeout: 5000 });
      } catch (e) { sidefejl.push("siden blev ikke klar: " + String(e.message).split("\n")[0]); }
    };
    return { ctx, side, sidefejl, hent };
  }
  const nulstil = () => { tilstand.json = base; tilstand.status = 200; tilstand.indlejret = null; };

  // ---------- 1. grafen: hver maaned 1..132 (11 aar), med og uden huller, paa fire bredder; lange raekker; kant-startmaaneder
  let antalGrafer = 0;
  const alleN = HURTIG ? [1, 2, 4, 6, 7, 8, 10, 11, 12, 13, 14, 22, 23, 24, 36, 41, 42, 60, 61, 66, 90, 120, 132]
                       : Array.from({ length: 132 }, (_, k) => k + 1);
  for (const bredde of [320, 390, 768, 1280]) {
    const { ctx, side, sidefejl, hent } = await aabn(bredde);
    const sager = [];
    for (const n of alleN) for (const medHul of [false, true]) if (!medHul || n >= 3) sager.push({ n, start: [2026, 8], medHul });
    for (const n of [240, 480]) sager.push({ n, start: [2026, 8], medHul: false });
    for (const start of [[2026, 12], [2027, 1], [2026, 11]]) for (const n of [1, 2, 6, 7, 13, 24, 42, 60, 120]) sager.push({ n, start, medHul: n >= 6 });
    for (const { n, start, medHul } of sager) {
      const huller = medHul ? new Set([1, Math.floor(n / 3), Math.floor(n / 2), n - 2].filter(k => k > 0 && k < n - 1)) : null;
      tilstand.json = hovedbog(n, start, huller);
      await hent();
      const m = await side.evaluate(maalGraf); antalGrafer++;
      const hvor = `graf ${bredde}px, ${n} mdr fra ${start.join("-")}${medHul ? ", med huller" : ""}`;
      if (!m) { F(hvor, "ingen graf"); continue; }
      for (const f of m.fund.slice(0, 3)) F(hvor, f);
      if (n <= 90 && m.prik) F(hvor, `${m.prik} prikker roerer hinanden`);
      if (n <= 90 && m.streg) F(hvor, `${m.streg} basisrate-streger gaar ind i nabokolonnen`);
      const nyeste = MND[(start[1] - 1 + n - 1) % 12];
      if (m.maaneder.length && m.maaneder[0] !== nyeste) F(hvor, `nyeste maaned (${nyeste}) er ikke maerket: ${m.maaneder.slice(0, 3).join(" ")}`);
      for (const f of sidefejl.splice(0)) F(hvor, "sidefejl: " + f);
    }
    await ctx.close();
  }
  nulstil();

  // ---------- 2. tekst: translitteration og dansk talformat gennem et felt, siden viser ordret
  {
    tilstand.json = kopi(base);
    tilstand.json.hovedbog_note = "Annonceringsdatoer foer 1979; ratioer saldoer scenarioer; koefficient Baa AAA; hash 6baeade4 dd6abb3b8a70aae1; "
      + "RAADETS_KONSENSUS RAADETS_2027; manifest_72c3371d.json; se BEDOEMMELSESNOEGLE.md. REKALIBRERING PAAKRAEVET; faerdig maaned raekke; "
      + "v5.0.1 15.1% 1,234 obs; diagnostik 4.5 og 4.4-bootstrap; DGS10-DTB3 BAA10Y; noegle.";
    const venter = "Annonceringsdatoer før 1979; ratioer saldoer scenarioer; koefficient Baa AAA; hash 6baeade4 dd6abb3b8a70aae1; "
      + "RAADETS_KONSENSUS RAADETS_2027; manifest_72c3371d.json; se BEDOEMMELSESNOEGLE.md. REKALIBRERING PÅKRÆVET; færdig måned række; "
      + "v5.0.1 15,1 % 1 234 obs; diagnostik 4.5 og 4.4-bootstrap; DGS10-DTB3 BAA10Y; nøgle.";
    const { ctx, side, sidefejl, hent } = await aabn(1280);
    await hent();
    const t = await side.evaluate(() => document.body.innerText);
    if (!t.includes(venter)) { const i = t.indexOf("Annonceringsdato"); F("tekst", "uventet gengivelse: " + JSON.stringify(t.slice(i, i + venter.length + 10))); }
    for (const f of sidefejl) F("tekst", "sidefejl: " + f);
    await ctx.close(); nulstil();
  }

  // ---------- 3. raekkens felter: et hul, en 2027-raekke med de uscorede felter og en note med en hash
  for (const bredde of [360, 1280]) {
    tilstand.json = kopi(base);
    const hb = tilstand.json.hovedbog = [
      Object.assign({}, sidste, { logget: "2026-08-12", snapshot: "2026-08-12", note: "", kalibrering: "", vindue: "", input: "", P_maanedlig: "" }),
      Object.assign({}, sidste, { logget: "2026-09-10", snapshot: "2026-09-10", kalibrering: "72c3371d", vindue: "", input: "", P_maanedlig: "",
        note: "bro: P(v? 6baeade4)=15.0% / P(v5.0.1 72c3371d)=15.1% ved identiske inputs (BEDOEMMELSESNOEGLE.md)" }),
      hul("2026-10"),
      Object.assign({}, sidste, { logget: "2026-11-10", snapshot: "2026-11-10", kalibrering: "aae10f3c", vindue: "2026-11..2027-10", input: "daglig 2026-10-10..2026-11-09 (21d)",
        P_maanedlig: "15.6%", P_maanedligt_fit: "16.2%", P_1953Q2: "17.0%", P_1960Q1: "16.5%", note: "" }),
    ];
    const { ctx, side, sidefejl, hent } = await aabn(bredde);
    await hent();
    const t = await side.evaluate(() => document.body.innerText);
    for (const s of ["Kalibrering: aae10f3c", "Input: daglig 2026-10-10..2026-11-09 (21d)", "P på månedstal (sammenligning): 15,6 %",
      "Uscoret, månedligt fit: 16,2 %", "Uscoret, start 1953Q2: 17,0 %", "Uscoret, start 1960Q1: 16,5 %", "2026-10 (ikke logget)",
      "Note: ingen række i logvinduet", "Note: bro: P(v? 6baeade4)=15,0 % / P(v5.0.1 72c3371d)=15,1 % ved identiske inputs (BEDOEMMELSESNOEGLE.md)",
      "En tom måned er en måned uden læsning i logvinduet."])
      if (!t.includes(s)) F(`raekkefelter ${bredde}px`, "mangler: " + s);
    const m = await side.evaluate(() => {
      const felt = document.querySelector(".hb-tabel");
      if (!felt) return null;
      const f = felt.getBoundingClientRect();
      return { klasser: [...felt.querySelectorAll("tbody tr")].map(tr => tr.className || "-").join(","),
        udenfor: [...felt.querySelectorAll("tr.detalje div")].map(e => e.getBoundingClientRect()).filter(d => d.right > f.right + 0.6 || d.left < f.left - 0.6).length,
        ruller: document.documentElement.scrollWidth > document.documentElement.clientWidth };
    });
    if (!m) { F(`raekkefelter ${bredde}px`, "hovedbogstabellen (.hb-tabel) findes ikke"); await ctx.close(); nulstil(); continue; }
    // nyeste oeverst: 2026-11 (felter), hullet (note), 2026-09 (felter), 2026-08 (ingen felter, ingen ekstra linje)
    if (m.klasser !== "har-detalje,detalje,har-detalje,detalje,har-detalje,detalje,-") F(`raekkefelter ${bredde}px`, "uventede tabelraekker: " + m.klasser);
    if (m.udenfor) F(`raekkefelter ${bredde}px`, `${m.udenfor} feltlinjer rager ud over det synlige felt`);
    if (m.ruller) F(`raekkefelter ${bredde}px`, "siden ruller vandret");
    if (hb.length !== 4) F("raekkefelter", "testens egen opstilling er aendret");
    for (const f of sidefejl) F(`raekkefelter ${bredde}px`, "sidefejl: " + f);
    await ctx.close(); nulstil();
  }

  // ---------- 4. fejlstier: aldrig en halv side, altid en besked og filvaelgeren
  async function fejlsti(navn, opsaet, tjek) {
    nulstil(); opsaet();
    const { ctx, side, sidefejl, hent } = await aabn(1280);
    await hent();
    const s = await side.evaluate(() => ({ besked: (document.getElementById("indlaes-tekst") || {}).textContent || "", tekst: document.body.innerText,
      vaelger: !!document.getElementById("vaelg") && !document.getElementById("vaelg").hidden, tegnet: !!document.querySelector("h1"), sektioner: document.querySelectorAll("section").length }));
    try { await tjek(s, side); } catch (e) { F(navn, "kunne ikke gennemfoeres: " + String(e.message).split("\n")[0]); }
    for (const f of sidefejl) F(navn, "sidefejl: " + f);
    await ctx.close(); nulstil();
  }
  const udenBaand = () => { const d = kopi(base); delete d.baand; return d; };
  await fejlsti("manglende felt", () => { tilstand.json = udenBaand(); }, async s => {
    if (!/kunne ikke vises/.test(s.besked) || !s.vaelger) F("manglende felt", "ingen besked eller filvaelger: " + JSON.stringify(s.besked));
    if (s.tegnet || s.sektioner) F("manglende felt", "en halv side staar tilbage");
  });
  await fejlsti("ugyldig JSON", () => { tilstand.json = "{ikke json"; }, async s => {
    if (!/kunne ikke hentes/.test(s.besked) || !s.vaelger || s.tegnet) F("ugyldig JSON", JSON.stringify(s.besked));
  });
  await fejlsti("indlejret kopi", () => { tilstand.status = 404; tilstand.indlejret = JSON.stringify(base).replace(/</g, "\\u003c"); }, async s => {
    if (!s.tegnet || s.sektioner < 6) F("indlejret kopi", "siden blev ikke tegnet fra den indlejrede kopi");
  });
  await fejlsti("indlejret kopi med manglende felt", () => { tilstand.status = 404; tilstand.indlejret = JSON.stringify(udenBaand()).replace(/</g, "\\u003c"); }, async s => {
    if (!/kunne ikke vises/.test(s.besked) || s.tegnet) F("indlejret kopi med manglende felt", JSON.stringify(s.besked));
  });
  await fejlsti("tom hovedbog", () => { tilstand.json = Object.assign(kopi(base), { hovedbog: [] }); }, async s => {
    if (!s.tegnet || !/Ingen logførte rækker endnu/.test(s.tekst)) F("tom hovedbog", "vises ikke rigtigt");
  });
  await fejlsti("filvaelgeren", () => { tilstand.status = 404; }, async (s, side) => {
    if (!/kunne ikke hentes/.test(s.besked) || !s.vaelger) F("filvaelgeren", "404 gav ingen besked: " + JSON.stringify(s.besked));
    const mappe = fs.mkdtempSync(path.join(os.tmpdir(), "dashboard-tjek-"));
    const fil = (navn, indhold) => { const f = path.join(mappe, navn); fs.writeFileSync(f, indhold); return f; };
    const besked = () => side.evaluate(() => (document.getElementById("indlaes-tekst") || {}).textContent || "");
    await side.setInputFiles("#fil", fil("ugyldig.json", "{ikke json"), { timeout: 3000 }); await side.waitForTimeout(150);
    if (!/ikke gyldig JSON/.test(await besked())) F("filvaelgeren", "ugyldig fil: " + await besked());
    await side.setInputFiles("#fil", fil("halv.json", JSON.stringify(udenBaand())), { timeout: 3000 }); await side.waitForTimeout(150);
    if (!/kunne ikke vises/.test(await besked())) F("filvaelgeren", "fil der ikke kan tegnes: " + await besked());
    await side.setInputFiles("#fil", fil("ok.json", JSON.stringify(base)), { timeout: 3000 }); await side.waitForTimeout(250);
    if (!await side.evaluate(() => !!document.querySelector("h1") && document.querySelectorAll("section").length > 5 && !document.getElementById("indlaes")))
      F("filvaelgeren", "den rigtige fil blev ikke vist efter to fejl");
    fs.rmSync(mappe, { recursive: true, force: true });
  });

  // ---------- 5. den committede dashboard.json, som den er: lys og moerk, fire bredder
  const medFelter = base.hovedbog.filter(r => ["kalibrering", "input", "P_maanedlig", "P_maanedligt_fit", "P_1953Q2", "P_1960Q1", "note"].some(k => typeof r[k] === "string" && r[k].trim())).length;
  for (const bredde of [320, 390, 768, 1280]) for (const skema of ["light", "dark"]) {
    const { ctx, side, sidefejl, hent } = await aabn(bredde, skema);
    await hent();
    const hvor = `committet dashboard.json ${bredde}px ${skema}`;
    const g = await side.evaluate(maalGraf);
    for (const f of (g ? g.fund : ["ingen hovedbogsgraf"])) F(hvor, f);
    const m = await side.evaluate(() => ({ t: document.body.innerText, felter: document.querySelectorAll(".hb-tabel tr.detalje").length, raekker: document.querySelectorAll(".hb-tabel tbody tr:not(.detalje)").length,
      sektioner: document.querySelectorAll("section").length, ruller: document.documentElement.scrollWidth > document.documentElement.clientWidth }));
    if (m.raekker !== base.hovedbog.length || m.felter !== medFelter) F(hvor, `ventede ${base.hovedbog.length} raekker og ${medFelter} feltlinjer, fik ${m.raekker} og ${m.felter}`);
    if (m.sektioner < 8) F(hvor, `kun ${m.sektioner} sektioner`);
    if (m.ruller) F(hvor, "siden ruller vandret");
    if (/BEDØMMELSESNØGLE|datør\b/.test(m.t)) F(hvor, "et filnavn eller 'datoer' er translittereret");
    for (const r of base.hovedbog) if (r.kalibrering && !m.t.includes("Kalibrering: " + r.kalibrering)) F(hvor, "raekkens kalibrering staar ikke ordret: " + r.kalibrering);
    for (const f of sidefejl) F(hvor, "sidefejl: " + f);
    await ctx.close();
  }

  await browser.close(); srv.close();
  console.log(`dashboard_tjek: ${antalGrafer} grafer, tekst, raekkefelter, 6 fejlstier og den committede dashboard.json paa 4 bredder`);
  if (fejl.length) { console.log(`${fejl.length} FEJL:`); for (const f of fejl.slice(0, 40)) console.log("  " + f); if (fejl.length > 40) console.log(`  ... og ${fejl.length - 40} til`); }
  else console.log("ALT OK");
  process.exit(fejl.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
