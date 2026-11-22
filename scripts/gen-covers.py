#!/usr/bin/env python3
"""Regenerate the cover images (docs/assets/images/covers/*.svg, also used as link
previews) and the LDAPS guide illustrations. Usage: python3 scripts/gen-covers.py ."""
import os, sys
from xml.sax.saxutils import escape as esc

ROOT = sys.argv[1]
COVERS = os.path.join(ROOT, "docs/assets/images/covers")
ADIMG = os.path.join(ROOT, "docs/how-to/active-directory/images")
os.makedirs(COVERS, exist_ok=True)
os.makedirs(ADIMG, exist_ok=True)

SANS = "Inter, 'Segoe UI', 'DejaVu Sans', Roboto, Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'DejaVu Sans Mono', Consolas, Menlo, monospace"
FG, MUTED, LINE, BOX, CYAN, TEAL = "#e2e8f0", "#94a3b8", "#38bdf8", "#0a1d40", "#38bdf8", "#2dd4bf"
RED, GREEN, AMBER = "#f87171", "#4ade80", "#fbbf24"


def t(x, y, s, size=18, fill=FG, weight=400, anchor="start", font=SANS, extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family="{font}" {extra}>{esc(s)}</text>')


def box(x, y, w, h, title=None, sub=None, stroke=LINE, op=".55", fill=BOX, size=22, rx=14, sw=1.5):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-opacity="{op}" stroke-width="{sw}"/>']
    cx = x + w / 2
    if title and sub:
        out.append(t(cx, y + h / 2 - 4, title, size, weight=700, anchor="middle"))
        out.append(t(cx, y + h / 2 + 22, sub, 15, MUTED, anchor="middle"))
    elif title:
        out.append(t(cx, y + h / 2 + size / 3, title, size, weight=700, anchor="middle"))
    return "".join(out)


def arrow(d, color=CYAN, dash=False, w=2.5):
    da = ' stroke-dasharray="7 6"' if dash else ""
    return f'<path d="{d}" stroke="{color}" stroke-width="{w}" fill="none" marker-end="url(#a)"{da}/>'


def pill(x, y, label, color=CYAN, size=15, w=None):
    w = w or (len(label) * size * 0.62 + 28)
    return (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{size + 16}" rx="{(size + 16) / 2}" fill="{color}" fill-opacity=".14" stroke="{color}" stroke-opacity=".6"/>'
            + t(x + w / 2, y + size + 3, label, size, color, 700, "middle"))


def terminal(x, y, w, h, lines, title="bash"):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#020b1c" stroke="{LINE}" stroke-opacity=".45"/>',
           f'<rect x="{x}" y="{y}" width="{w}" height="38" rx="14" fill="#0b1f45"/>',
           f'<rect x="{x}" y="{y + 24}" width="{w}" height="14" fill="#0b1f45"/>']
    for i, c in enumerate(["#f87171", "#fbbf24", "#4ade80"]):
        out.append(f'<circle cx="{x + 24 + i * 22}" cy="{y + 19}" r="6.5" fill="{c}"/>')
    out.append(t(x + w / 2, y + 25, title, 15, MUTED, anchor="middle", font=MONO))
    yy = y + 74
    for ln in lines:
        if ln.startswith("$ "):
            out.append(f'<text x="{x + 22}" y="{yy}" font-size="18" font-family="{MONO}"><tspan fill="{TEAL}">$ </tspan><tspan fill="{FG}">{esc(ln[2:])}</tspan></text>')
        elif ln.startswith("# "):
            out.append(t(x + 22, yy, ln, 17, "#64748b", font=MONO))
        elif ln.startswith("! "):
            out.append(t(x + 22, yy, ln[2:], 17, GREEN, font=MONO))
        else:
            out.append(t(x + 22, yy, ln, 17, MUTED, font=MONO))
        yy += 32
    return "".join(out)


DEFS = f'''<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#04132e"/><stop offset="1" stop-color="#0b1f45"/></linearGradient>
<linearGradient id="brand" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#60a5fa"/><stop offset="1" stop-color="#2dd4bf"/></linearGradient>
<radialGradient id="glow" cx="0.8" cy="0.2" r="0.6"><stop offset="0" stop-color="#2563eb" stop-opacity=".28"/><stop offset="1" stop-color="#2563eb" stop-opacity="0"/></radialGradient>
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#1e3a8a" stroke-opacity=".25"/></pattern>
<marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="{CYAN}"/></marker>
</defs>'''


def cover(name, kind, topic, title_lines, subtitle, diagram, desc):
    title = " ".join(title_lines)
    eyebrow = f"{kind} · {topic}".upper()
    body = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="t d">',
            f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>', DEFS,
            '<rect width="1200" height="630" fill="url(#bg)"/>',
            '<rect width="1200" height="630" fill="url(#grid)"/>',
            '<rect width="1200" height="630" fill="url(#glow)"/>',
            '<rect width="1200" height="8" fill="url(#brand)"/>',
            pill(60, 58, eyebrow, TEAL if kind == "How-To" else CYAN, 15)]
    size = 50 if max(len(l) for l in title_lines) <= 17 else 44
    y = 168
    for ln in title_lines:
        body.append(t(60, y, ln, size, "#ffffff", 800))
        y += size * 1.18
    yy = y + 14
    for ln in subtitle:
        body.append(t(60, yy, ln, 21, MUTED))
        yy += 30
    body.append('<rect x="60" y="548" width="44" height="4" rx="2" fill="url(#brand)"/>')
    body.append(t(60, 586, "bhry98.github.io", 20, FG, 700))
    body.append(t(232, 586, "· Abdelrahman Mahmoud", 20, MUTED))
    body.append(f'<g>{diagram}</g></svg>')
    with open(os.path.join(COVERS, name + ".svg"), "w") as f:
        f.write("\n".join(body))


# ---------------------------------------------------------------- diagrams
X0 = 610  # left edge of diagram area

d_install_nginx = terminal(X0, 110, 545, 400, [
    "# RHEL / Rocky / Fedora",
    "$ sudo dnf install -y nginx",
    "$ sudo systemctl enable --now nginx",
    "$ sudo firewall-cmd --add-service=http",
    "$ curl -I http://localhost",
    "! HTTP/1.1 200 OK",
    "Server: nginx/1.28.0",
    "$ nginx -t",
    "! syntax is ok · test is successful",
], "root@web01: ~")

d_nginx_ha = "".join([
    box(760, 96, 240, 52, "Clients", size=20),
    arrow("M880 148 V186"),
    pill(795, 192, "VIP 10.0.0.100", AMBER, 15, 170),
    arrow("M880 223 V258"),
    f'<rect x="{X0+10}" y="262" width="530" height="128" rx="16" fill="none" stroke="{TEAL}" stroke-opacity=".5" stroke-dasharray="7 6"/>',
    t(X0 + 28, 286, "keepalived (VRRP)", 15, TEAL, 700),
    box(X0 + 40, 298, 210, 74, "nginx-1", "MASTER", stroke=TEAL, op=".8"),
    box(X0 + 300, 298, 210, 74, "nginx-2", "BACKUP"),
    arrow(f"M{X0+145} 372 L{X0+110} 446"), arrow(f"M{X0+145} 372 L{X0+275} 446"), arrow(f"M{X0+145} 372 L{X0+440} 446"),
    arrow(f"M{X0+405} 372 L{X0+125} 446", dash=True), arrow(f"M{X0+405} 372 L{X0+275} 446", dash=True), arrow(f"M{X0+405} 372 L{X0+425} 446", dash=True),
    box(X0 + 20, 452, 160, 64, "app-1", ":8080", size=19),
    box(X0 + 195, 452, 160, 64, "app-2", ":8080", size=19),
    box(X0 + 370, 452, 160, 64, "app-3", ":8080", size=19),
    t(X0 + 275, 548, "upstream · least_conn · health checks", 15, MUTED, anchor="middle"),
])

d_what_nginx = "".join([
    box(X0, 150, 130, 60, "Browser", size=18), box(X0, 250, 130, 60, "Mobile", size=18), box(X0, 350, 130, 60, "API client", size=17),
    arrow(f"M{X0+130} 180 L{X0+178} 250"), arrow(f"M{X0+130} 280 H{X0+178}"), arrow(f"M{X0+130} 380 L{X0+178} 310"),
    f'<rect x="{X0+185}" y="120" width="200" height="330" rx="16" fill="{BOX}" stroke="url(#brand)" stroke-width="2.5"/>',
    t(X0 + 285, 162, "NGINX", 28, "#ffffff", 800, "middle"),
    *[pill(X0 + 205, 182 + i * 50, lbl, c, 14, 160) for i, (lbl, c) in enumerate([
        ("TLS / HTTPS", TEAL), ("Reverse proxy", CYAN), ("Load balancer", CYAN), ("Static files", CYAN), ("Cache · gzip", CYAN)])],
    arrow(f"M{X0+385} 220 H{X0+430}"), arrow(f"M{X0+385} 285 H{X0+430}"), arrow(f"M{X0+385} 350 H{X0+430}"),
    box(X0 + 435, 190, 120, 56, "app :8080", size=16), box(X0 + 435, 258, 120, 56, "app :8081", size=16), box(X0 + 435, 326, 120, 56, "api :3000", size=16),
    t(X0 + 285, 490, "one entry point · many backends", 16, MUTED, anchor="middle"),
])


def commit(cx, cy, c=CYAN):
    return f'<circle cx="{cx}" cy="{cy}" r="13" fill="#04132e" stroke="{c}" stroke-width="4"/>'


d_git = "".join([
    f'<path d="M{X0+20} 200 H{X0+540}" stroke="{CYAN}" stroke-width="4"/>',
    f'<path d="M{X0+150} 200 C{X0+190} 200 {X0+190} 290 {X0+230} 290 H{X0+370} C{X0+410} 290 {X0+410} 200 {X0+450} 200" stroke="{TEAL}" stroke-width="4" fill="none"/>',
    *[commit(X0 + x, 200) for x in (40, 150, 290, 450, 530)],
    *[commit(X0 + x, 290, TEAL) for x in (240, 320)],
    t(X0 + 20, 170, "main", 17, CYAN, 700, font=MONO), t(X0 + 232, 328, "feature/login", 16, TEAL, 700, font=MONO),
    t(X0 + 450, 170, "merge", 15, MUTED, anchor="middle", font=MONO),
    *[box(X0 + 10 + i * 180, 380, 165, 70, n, s, size=19) for i, (n, s) in enumerate([("GitHub", "Microsoft"), ("GitLab", "self-host / SaaS"), ("Bitbucket", "Atlassian")])],
    t(X0 + 275, 492, "Git = the tool · these = hosting platforms", 16, MUTED, anchor="middle"),
])

d_install_git = terminal(X0, 110, 545, 400, [
    "$ git --version",
    "! git version 2.51.0",
    '$ git config --global user.name "Your Name"',
    "$ git config --global user.email you@mail.com",
    "$ git config --global init.defaultBranch main",
    "$ ssh-keygen -t ed25519",
    "$ ssh -T git@github.com",
    "! Hi you! You've successfully authenticated",
], "~/projects")


def stack(x, y, w, layers, title):
    out = [t(x + w / 2, y - 14, title, 19, "#ffffff", 700, "middle")]
    yy = y
    for lbl, c, h in layers:
        if isinstance(lbl, list):
            n = len(lbl); gw = (w - (n - 1) * 8) / n
            for i, l in enumerate(lbl):
                out.append(f'<rect x="{x + i * (gw + 8):.0f}" y="{yy}" width="{gw:.0f}" height="{h}" rx="8" fill="{c}" fill-opacity=".18" stroke="{c}" stroke-opacity=".7"/>')
                out.append(t(x + i * (gw + 8) + gw / 2, yy + h / 2 + 6, l, 14, FG, 600, "middle"))
        else:
            out.append(f'<rect x="{x}" y="{yy}" width="{w}" height="{h}" rx="8" fill="{c}" fill-opacity=".18" stroke="{c}" stroke-opacity=".7"/>')
            out.append(t(x + w / 2, yy + h / 2 + 6, lbl, 15, FG, 600, "middle"))
        yy += h + 8
    return "".join(out)


d_containers = "".join([
    stack(X0 + 5, 140, 255, [
        (["App A", "App B"], TEAL, 46), (["Libs", "Libs"], TEAL, 40), (["Guest OS", "Guest OS"], AMBER, 52),
        ("Hypervisor", CYAN, 44), ("Host OS · Hardware", "#64748b", 44)], "Virtual machines"),
    stack(X0 + 290, 140, 255, [
        (["App A", "App B", "App C"], TEAL, 46), (["Libs", "Libs", "Libs"], TEAL, 40),
        ("Container runtime", CYAN, 52), ("Host OS (shared kernel)", AMBER, 44), ("Hardware", "#64748b", 44)], "Containers"),
    t(X0 + 132, 470, "GBs · minutes to boot", 16, MUTED, anchor="middle"),
    t(X0 + 417, 470, "MBs · seconds to start", 16, GREEN, anchor="middle"),
])

d_jdk = "".join([
    f'<rect x="{X0}" y="110" width="545" height="420" rx="18" fill="{CYAN}" fill-opacity=".08" stroke="{CYAN}" stroke-opacity=".7" stroke-width="2"/>',
    t(X0 + 24, 146, "JDK", 30, CYAN, 800), t(X0 + 92, 146, "develop · javac · jar · jdb · jshell", 16, MUTED),
    f'<rect x="{X0+30}" y="172" width="485" height="330" rx="16" fill="{TEAL}" fill-opacity=".08" stroke="{TEAL}" stroke-opacity=".7" stroke-width="2"/>',
    t(X0 + 52, 208, "JRE", 28, TEAL, 800), t(X0 + 116, 208, "run · class libraries (java.*)", 16, MUTED),
    f'<rect x="{X0+60}" y="236" width="425" height="240" rx="14" fill="{AMBER}" fill-opacity=".08" stroke="{AMBER}" stroke-opacity=".75" stroke-width="2"/>',
    t(X0 + 82, 272, "JVM", 26, AMBER, 800), t(X0 + 146, 272, "executes bytecode", 16, MUTED),
    *[pill(X0 + 82 + (i % 2) * 196, 296 + (i // 2) * 50, l, AMBER, 14, 180) for i, l in enumerate(
        ["Class loader", "JIT compiler", "Garbage collector", "Interpreter", "Memory: heap · stack", "Native interface"])],
])

d_lts = "".join([
    f'<path d="M{X0} 470 H{X0+545}" stroke="#64748b" stroke-width="2"/>',
    *[t(X0 + 20 + i * 104, 500, y, 15, MUTED, anchor="middle") for i, y in enumerate(["2021", "2022", "2023", "2024", "2025", "2026"])],
    *["".join([f'<rect x="{X0 + x}" y="{y}" width="{w}" height="30" rx="7" fill="{c}" fill-opacity="{o}" stroke="{c}"/>',
               t(X0 + x + 10, y + 21, lbl, 15, "#ffffff", 700)])
      for (x, y, w, c, o, lbl) in [
          (20, 140, 525, TEAL, ".35", "Java 17 LTS: supported for years"),
          (120, 190, 60, "#64748b", ".3", "18"), (175, 230, 60, "#64748b", ".3", "19"), (225, 270, 60, "#64748b", ".3", "20"),
          (280, 320, 265, TEAL, ".35", "Java 21 LTS"),
          (335, 370, 60, "#64748b", ".3", "22"), (385, 410, 60, "#64748b", ".3", "23"),
      ]],
    pill(X0 + 290, 96, "LTS = Long-Term Support", AMBER, 15),
    t(X0 + 20, 545, "non-LTS: ~6 months of updates", 15, MUTED),
])

d_s3 = "".join([
    box(X0 + 175, 100, 200, 64, "Your app", "SDK / REST API", size=20),
    arrow(f"M{X0+230} 164 L{X0+130} 226"), arrow(f"M{X0+320} 164 L{X0+420} 226"),
    t(X0 + 130, 214, "write()", 15, MUTED, anchor="end", font=MONO), t(X0 + 425, 214, "PUT object", 15, MUTED, font=MONO),
    f'<rect x="{X0}" y="232" width="250" height="250" rx="16" fill="{BOX}" stroke="{AMBER}" stroke-opacity=".6"/>',
    t(X0 + 125, 268, "Local disk", 21, "#ffffff", 700, "middle"),
    *[t(X0 + 28, 310 + i * 30, l, 16, MUTED, font=MONO) for i, l in enumerate(["/var/app/uploads/", "  ├─ 2026/", "  │  └─ invoice.pdf", "  └─ avatar.png"])],
    t(X0 + 125, 455, "1 server · 1 disk", 15, AMBER, 700, "middle"),
    f'<rect x="{X0+295}" y="232" width="250" height="250" rx="16" fill="{BOX}" stroke="{TEAL}" stroke-opacity=".7"/>',
    t(X0 + 420, 268, "S3 bucket", 21, "#ffffff", 700, "middle"),
    *[pill(X0 + 315, 290 + i * 42, l, TEAL, 13, 210) for i, l in enumerate(["invoices/2026/inv-01.pdf", "avatars/u42.png", "backups/db.sql.gz"])],
    t(X0 + 420, 455, "any server · HTTP · replicated", 15, TEAL, 700, "middle"),
])


def node(x, y, w, label, c=CYAN):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="44" rx="10" fill="{BOX}" stroke="{c}" stroke-opacity=".75"/>'
            + t(x + w / 2, y + 28, label, 15, FG, 600, "middle", MONO))


d_ldap = "".join([
    node(X0 + 160, 110, 230, "dc=bhry98,dc=local", TEAL),
    f'<path d="M{X0+275} 154 V184 M{X0+120} 184 H{X0+430} M{X0+120} 184 V208 M{X0+430} 184 V208" stroke="{LINE}" stroke-opacity=".6" stroke-width="2" fill="none"/>',
    node(X0 + 40, 208, 160, "ou=Users"), node(X0 + 350, 208, 160, "ou=Groups"),
    f'<path d="M{X0+120} 252 V276 M{X0+50} 276 H{X0+190} M{X0+50} 276 V300 M{X0+190} 276 V300" stroke="{LINE}" stroke-opacity=".6" stroke-width="2" fill="none"/>',
    f'<path d="M{X0+430} 252 V300" stroke="{LINE}" stroke-opacity=".6" stroke-width="2" fill="none"/>',
    node(X0 - 10, 300, 130, "cn=alice", AMBER), node(X0 + 130, 300, 130, "cn=bob", AMBER), node(X0 + 350, 300, 160, "cn=devs", AMBER),
    *[box(X0 + i * 188, 398, 170, 70, n, s, size=18) for i, (n, s) in enumerate([("Active Directory", "Microsoft"), ("OpenLDAP", "open source"), ("FreeIPA / 389DS", "Red Hat")])],
    t(X0 + 275, 505, "one protocol (LDAP v3) · many directory servers", 15, MUTED, anchor="middle"),
])

d_ldaps = "".join([
    box(X0, 120, 170, 80, "Keycloak", "LDAP client", size=20),
    box(X0, 250, 170, 80, "Linux / Java", "ldapsearch", size=20),
    box(X0, 380, 170, 80, "Apps", "Jenkins, GitLab…", size=20),
    f'<rect x="{X0+375}" y="170" width="170" height="240" rx="16" fill="{BOX}" stroke="url(#brand)" stroke-width="2.5"/>',
    t(X0 + 460, 220, "DC01", 26, "#ffffff", 800, "middle"), t(X0 + 460, 248, "bhry98.local", 15, MUTED, anchor="middle"),
    pill(X0 + 395, 272, "AD DS", CYAN, 14, 130), pill(X0 + 395, 316, "AD CS (CA)", TEAL, 14, 130),
    t(X0 + 460, 386, "WS 2025", 15, MUTED, anchor="middle"),
    arrow(f"M{X0+170} 160 L{X0+370} 230", TEAL, w=3), arrow(f"M{X0+170} 290 H{X0+370}", TEAL, w=3), arrow(f"M{X0+170} 420 L{X0+370} 350", TEAL, w=3),
    pill(X0 + 205, 262, "ldaps:// 636  TLS", TEAL, 14, 150),
    f'<g transform="translate({X0+262},170)"><rect x="0" y="14" width="26" height="22" rx="4" fill="{TEAL}"/><path d="M5 14 V8 a8 8 0 0 1 16 0 V14" stroke="{TEAL}" stroke-width="4" fill="none"/></g>',
    t(X0 + 270, 505, "389 plain text  >>  636 encrypted (TLS)", 17, FG, 700, "middle"),
])

d_spring_kc = "".join([
    box(X0, 110, 180, 70, "Client app", "Angular · mobile", size=19),
    box(X0 + 365, 110, 180, 70, "Keycloak", "realm: company", stroke=TEAL, op=".85", size=19),
    box(X0 + 180, 380, 190, 80, "Spring Boot API", "resource server", size=19),
    arrow(f"M{X0+180} 135 H{X0+360}"), t(X0 + 272, 126, "1. log in", 15, MUTED, anchor="middle"),
    arrow(f"M{X0+365} 165 H{X0+186}"), t(X0 + 275, 192, "2. access token (JWT)", 15, MUTED, anchor="middle"),
    arrow(f"M{X0+90} 180 L{X0+220} 374"), t(X0 + 70, 300, "3. Bearer token", 15, MUTED),
    arrow(f"M{X0+455} 180 L{X0+340} 374", TEAL, True), t(X0 + 420, 300, "4. public keys", 15, MUTED),
    pill(X0 + 150, 490, "@PreAuthorize(\"hasRole('orders.read')\")", AMBER, 13, 260),
])

d_debug = "".join([
    terminal(X0, 100, 545, 250, [
        "$ oc get pods",
        "NAME            READY  STATUS",
        "orders-7d9f-x2  0/1    CrashLoopBackOff",
        "$ oc logs orders-7d9f-x2 --previous",
        "$ oc debug deployment/orders",
    ], "oc · orders-dev"),
    *[pill(X0 + (i % 3) * 185, 380 + (i // 3) * 52, l, c, 14, 175) for i, (l, c) in enumerate([
        ("Pending", AMBER), ("ImagePullBackOff", RED), ("CrashLoopBackOff", RED),
        ("OOMKilled (137)", RED), ("ConfigError", AMBER), ("Running 0/1", AMBER)])],
])

COVERS_SPEC = [
    ("nginx-install", "How-To", "Nginx", ["How to install", "Nginx"], ["Ubuntu, Debian, RHEL, Rocky,", "Docker and Windows"], d_install_nginx,
     "Terminal showing Nginx installed with dnf, started with systemctl and answering HTTP 200."),
    ("nginx-reverse-proxy-ha", "How-To", "Nginx", ["Nginx reverse proxy,", "load balancing", "& high availability"], ["TLS, upstreams, health checks,", "keepalived VIP failover"], d_nginx_ha,
     "Clients reach a virtual IP held by two Nginx servers with keepalived; Nginx balances traffic across three application servers."),
    ("what-is-nginx", "Blog", "Infrastructure", ["What is Nginx", "and why do we", "use it?"], ["Web server, reverse proxy,", "load balancer and more"], d_what_nginx,
     "Browsers, mobile apps and API clients connect to Nginx, which handles TLS, proxying, load balancing, static files and caching in front of several backend apps."),
    ("what-is-git", "Blog", "DevOps", ["What is Git?", "GitHub vs GitLab", "vs Bitbucket"], ["Version control explained,", "platforms compared"], d_git,
     "A Git branch graph with a feature branch merged into main, above the hosting platforms GitHub, GitLab and Bitbucket."),
    ("git-install", "How-To", "Git", ["How to install", "Git"], ["Windows, macOS and Linux,", "plus first-time setup and SSH keys"], d_install_git,
     "Terminal showing git --version, git config for name and email, and an SSH key test against GitHub."),
    ("containers-vs-traditional", "Blog", "DevOps", ["Containers vs", "traditional", "deployment"], ["Bare metal, VMs and containers", "explained for developers"], d_containers,
     "Side-by-side stacks: virtual machines each carry a guest OS on a hypervisor, containers share the host kernel through a container runtime."),
    ("jdk-jre-jvm", "Blog", "Java", ["JDK vs JRE", "vs JVM"], ["What each one is, and which", "one you actually need"], d_jdk,
     "Nested boxes: the JDK contains the JRE, which contains the JVM with its class loader, JIT compiler and garbage collector."),
    ("what-is-lts", "Blog", "Fundamentals", ["What does LTS", "mean?"], ["Long-Term Support releases", "and how to choose a version"], d_lts,
     "Timeline of Java releases: LTS versions 17 and 21 get years of support while versions 18, 19, 20, 22 and 23 get about six months."),
    ("s3-vs-local-storage", "Blog", "Architecture", ["S3 object storage", "vs local storage"], ["Where should your application", "keep its files?"], d_s3,
     "An application writing files to a local disk folder on one server, compared with putting objects into an S3 bucket reachable over HTTP."),
    ("ldap-active-directory-openldap", "Blog", "Security", ["What is LDAP?", "Active Directory", "vs OpenLDAP"], ["Directories, DNs and the", "products that implement them"], d_ldap,
     "An LDAP directory tree under dc=bhry98,dc=local with Users and Groups, above three directory products: Active Directory, OpenLDAP and FreeIPA."),
    ("ad-ldaps", "How-To", "Active Directory", ["Secure Active", "Directory with", "LDAPS (636)"], ["Windows Server 2025,", "AD CS and bhry98.local"], d_ldaps,
     "Keycloak, Linux tools and applications connect over encrypted LDAPS on port 636 to domain controller DC01 of bhry98.local, which runs AD DS and AD CS."),
    ("spring-boot-keycloak", "How-To", "Spring Boot", ["Secure a Spring", "Boot API with", "Keycloak"], ["OAuth 2.0 resource server,", "JWT and role mapping"], d_spring_kc,
     "A client logs in to Keycloak, receives a JWT and calls a Spring Boot API, which validates the token with Keycloak's public keys."),
    ("openshift-debug-pods", "How-To", "OpenShift", ["How to debug", "pods on", "OpenShift"], ["Pending, CrashLoopBackOff,", "OOMKilled and more"], d_debug,
     "Terminal with oc get pods showing CrashLoopBackOff, oc logs --previous and oc debug, above common pod status labels."),
]

for spec in COVERS_SPEC:
    cover(*spec)

# ------------------------------------------------- Windows dialog illustrations
WF = "'Segoe UI', 'DejaVu Sans', Arial, sans-serif"


def wt(x, y, s, size=15, fill="#1f2937", weight=400, anchor="start"):
    return t(x, y, s, size, fill, weight, anchor, WF)


def window(w, h, title, inner, desc, name, note="Illustration · bhry98.local lab · Windows Server 2025"):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h + 34}" viewBox="0 0 {w} {h + 34}" role="img" aria-labelledby="t d">',
           f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>',
           f'<rect width="{w}" height="{h + 34}" fill="#e5e7eb"/>',
           f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff" stroke="#9ca3af"/>',
           f'<rect x="0" y="0" width="{w}" height="34" fill="#f3f4f6"/>',
           wt(14, 22, title, 13, "#111827"),
           f'<path d="M{w-96} 18 h12 M{w-60} 11 h11 v11 h-11z M{w-26} 11 l11 11 M{w-15} 11 l-11 11" stroke="#374151" stroke-width="1.4" fill="none"/>',
           inner,
           wt(w / 2, h + 23, note, 12, "#6b7280", anchor="middle"),
           '</svg>']
    with open(os.path.join(ADIMG, name + ".svg"), "w") as f:
        f.write("\n".join(out))


def wizard_nav(steps, active, x=20, y=110):
    out = []
    for i, s in enumerate(steps):
        if i == active:
            out.append(f'<rect x="{x - 8}" y="{y + i * 30 - 18}" width="170" height="26" fill="#cce4f7"/>')
        out.append(wt(x, y + i * 30, s, 14, "#0f172a" if i == active else "#475569", 600 if i == active else 400))
    return "".join(out)


def buttons(w, h, labels=("< Previous", "Next >", "Install", "Cancel"), primary=1):
    out = []
    x = w - len(labels) * 108 - 10
    for i, l in enumerate(labels):
        out.append(f'<rect x="{x + i * 108}" y="{h - 52}" width="96" height="30" fill="#f9fafb" stroke="{"#2563eb" if i == primary else "#9ca3af"}" stroke-width="{2 if i == primary else 1}"/>')
        out.append(wt(x + i * 108 + 48, h - 32, l, 13, "#111827", anchor="middle"))
    return "".join(out)


def check(x, y, label, on=True, bold=False):
    mark = f'<path d="M{x + 3} {y - 6} l4 5 l8 -10" stroke="#ffffff" stroke-width="2.4" fill="none"/>' if on else ""
    return (f'<rect x="{x}" y="{y - 13}" width="16" height="16" rx="2" fill="{"#2563eb" if on else "#ffffff"}" stroke="#475569"/>{mark}'
            + wt(x + 26, y, label, 14, "#111827", 700 if bold else 400))


def radio(x, y, label, on=False):
    dot = f'<circle cx="{x + 8}" cy="{y - 5}" r="4" fill="#2563eb"/>' if on else ""
    return f'<circle cx="{x + 8}" cy="{y - 5}" r="8" fill="#ffffff" stroke="#475569"/>{dot}' + wt(x + 26, y, label, 14, "#111827", 700 if on else 400)


def hl(x, y, w, h):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#dc2626" stroke-width="2.5" rx="3"/>'


W, H = 900, 560
# 1. Add Roles and Features: Server Roles
roles = ["Active Directory Certificate Services", "Active Directory Domain Services (Installed)", "Active Directory Federation Services",
         "DHCP Server", "DNS Server (Installed)", "File and Storage Services (2 of 12 installed)", "Hyper-V", "Web Server (IIS)"]
inner = [wt(24, 74, "Select server roles", 24, "#1e3a8a", 300), wt(W - 24, 64, "DESTINATION SERVER", 11, "#475569", anchor="end"),
         wt(W - 24, 82, "CA01.bhry98.local", 12, "#111827", anchor="end"),
         wizard_nav(["Before You Begin", "Installation Type", "Server Selection", "Server Roles", "Features", "AD CS", "Role Services", "Confirmation"], 3, 30, 130),
         wt(220, 130, "Select one or more roles to install on the selected server.", 14, "#111827"),
         wt(220, 160, "Roles", 14, "#111827", 600),
         f'<rect x="220" y="170" width="420" height="300" fill="#ffffff" stroke="#9ca3af"/>']
for i, r in enumerate(roles):
    inner.append(check(234, 198 + i * 32, r, on=(i in (0, 1, 4)), bold=(i == 0)))
inner += [hl(226, 180, 380, 28), wt(660, 160, "Description", 14, "#111827", 600),
          wt(660, 190, "Active Directory Certificate", 13, "#334155"), wt(660, 208, "Services (AD CS) is used to", 13, "#334155"),
          wt(660, 226, "create certification authorities", 13, "#334155"), wt(660, 244, "that issue and manage", 13, "#334155"),
          wt(660, 262, "certificates.", 13, "#334155"), buttons(W, H)]
window(W, H, "Add Roles and Features Wizard", "".join(inner),
       "Add Roles and Features Wizard on CA01.bhry98.local with Active Directory Certificate Services selected.", "01-add-adcs-role")

# 2. AD CS Configuration: Setup Type
inner = [wt(24, 74, "Setup Type", 24, "#1e3a8a", 300), wt(W - 24, 64, "DESTINATION SERVER", 11, "#475569", anchor="end"),
         wt(W - 24, 82, "CA01.bhry98.local", 12, "#111827", anchor="end"),
         wizard_nav(["Credentials", "Role Services", "Setup Type", "CA Type", "Private Key", "Cryptography", "CA Name", "Validity Period", "Certificate Database", "Confirmation"], 2, 30, 130),
         wt(220, 130, "Specify the setup type of the CA", 15, "#111827", 600),
         wt(220, 160, "Enterprise certification authorities (CAs) can use Active Directory Domain Services (AD DS)", 13, "#334155"),
         wt(220, 178, "to simplify the management of certificates.", 13, "#334155"),
         radio(230, 220, "Enterprise CA", True),
         wt(256, 244, "Enterprise CAs must be domain members and are typically online to issue", 13, "#334155"),
         wt(256, 262, "certificates or certificate policies.", 13, "#334155"),
         hl(222, 202, 150, 28),
         radio(230, 310, "Standalone CA"),
         wt(256, 334, "Standalone CAs can be members of a workgroup or domain and do not require", 13, "#334155"),
         wt(256, 352, "AD DS.", 13, "#334155"),
         buttons(W, H, ("< Previous", "Next >", "Configure", "Cancel"))]
window(W, H, "AD CS Configuration", "".join(inner),
       "AD CS Configuration wizard, Setup Type page, with Enterprise CA selected.", "02-enterprise-ca")

# 3. CA Name
inner = [wt(24, 74, "CA Name", 24, "#1e3a8a", 300), wt(W - 24, 64, "DESTINATION SERVER", 11, "#475569", anchor="end"),
         wt(W - 24, 82, "CA01.bhry98.local", 12, "#111827", anchor="end"),
         wizard_nav(["Credentials", "Role Services", "Setup Type", "CA Type", "Private Key", "Cryptography", "CA Name", "Validity Period", "Certificate Database", "Confirmation"], 6, 30, 130),
         wt(220, 130, "Specify the name of the CA", 15, "#111827", 600),
         wt(220, 170, "Common name for this CA:", 13, "#111827"),
         f'<rect x="220" y="180" width="620" height="28" fill="#ffffff" stroke="#6b7280"/>', wt(228, 199, "bhry98-CA01-CA", 14),
         hl(216, 176, 628, 36),
         wt(220, 240, "Distinguished name suffix:", 13, "#111827"),
         f'<rect x="220" y="250" width="620" height="28" fill="#ffffff" stroke="#6b7280"/>', wt(228, 269, "DC=bhry98,DC=local", 14),
         wt(220, 310, "Preview of distinguished name:", 13, "#111827"),
         f'<rect x="220" y="320" width="620" height="28" fill="#f3f4f6" stroke="#d1d5db"/>', wt(228, 339, "CN=bhry98-CA01-CA,DC=bhry98,DC=local", 14, "#374151"),
         buttons(W, H, ("< Previous", "Next >", "Configure", "Cancel"))]
window(W, H, "AD CS Configuration", "".join(inner),
       "AD CS Configuration wizard, CA Name page: common name bhry98-CA01-CA and suffix DC=bhry98,DC=local.", "03-ca-name")

# 4. GPO autoenrollment
W2, H2 = 700, 560
inner = [f'<rect x="16" y="48" width="{W2 - 32}" height="30" fill="#f9fafb"/>', wt(30, 68, "Enrollment Policy Configuration", 14, "#111827", 600),
         wt(30, 110, "Enroll user and computer certificates automatically", 14, "#111827"),
         wt(30, 150, "Configuration Model:", 14, "#111827"),
         f'<rect x="200" y="132" width="200" height="28" fill="#ffffff" stroke="#6b7280"/>', wt(210, 151, "Enabled", 14), wt(382, 151, "v", 13),
         hl(196, 128, 208, 36),
         check(30, 200, "Renew expired certificates, update pending certificates, and remove", True),
         wt(56, 220, "revoked certificates", 14, "#111827"),
         check(30, 256, "Update certificates that use certificate templates", True),
         hl(24, 182, 640, 90),
         check(30, 310, "Log expiry events and show expiry notifications when the percentage", False),
         wt(56, 330, "of remaining certificate lifetime is", 14, "#111827"),
         wt(30, 380, "Group Policy: Default Domain Controllers Policy", 13, "#475569"),
         wt(30, 402, "Computer Configuration › Policies › Windows Settings › Security Settings ›", 13, "#475569"),
         wt(30, 422, "Public Key Policies › Certificate Services Client - Auto-Enrollment", 13, "#475569"),
         buttons(W2, H2, ("OK", "Cancel", "Apply"), 0)]
window(W2, H2, "Certificate Services Client - Auto-Enrollment Properties", "".join(inner),
       "Group Policy dialog Certificate Services Client - Auto-Enrollment set to Enabled with renew and update options checked.", "04-gpo-autoenroll")

# 5. certlm Personal store
W3, H3 = 1140, 420
cols = [(190, "Issued To"), (165, "Issued By"), (100, "Expiration"), (270, "Intended Purposes"), (170, "Template")]
inner = [wt(14, 62, "File    Action    View    Help", 13, "#111827"),
         f'<rect x="0" y="74" width="220" height="{H3 - 74}" fill="#f9fafb" stroke="#d1d5db"/>',
         wt(14, 100, "Certificates - Local Computer", 13, "#111827"), wt(28, 124, "v  Personal", 13, "#111827", 600),
         f'<rect x="40" y="132" width="110" height="22" fill="#cce4f7"/>', wt(48, 148, "Certificates", 13, "#111827"),
         wt(28, 176, "› Trusted Root Certification…", 13, "#111827"), wt(28, 200, "› Enterprise Trust", 13, "#111827"),
         wt(28, 224, "› Intermediate Certification…", 13, "#111827")]
x = 232
for w_, h_ in cols:
    inner.append(wt(x, 100, h_, 13, "#475569", 600)); x += w_
rows = [("DC01.bhry98.local", "bhry98-CA01-CA", "11/22/2027", "Client Authentication, Server Auth...", "Kerberos Authentication"),
        ("DC01.bhry98.local", "bhry98-CA01-CA", "11/22/2027", "Client Authentication, Server Auth...", "Domain Controller")]
for r, row in enumerate(rows):
    y = 130 + r * 30
    if r == 0:
        inner.append(f'<rect x="226" y="{y - 19}" width="{W3 - 236}" height="27" fill="#cce4f7"/>')
    x = 232
    for (w_, _), v in zip(cols, row):
        inner.append(wt(x, y, v, 13, "#111827")); x += w_
inner += [hl(226, 108, W3 - 236, 58),
          wt(232, 230, "Server Authentication (1.3.6.1.5.5.7.3.1) in Intended Purposes + the DC's FQDN as subject/SAN", 13, "#1e3a8a"),
          wt(232, 250, "= Active Directory will use this certificate for LDAPS on ports 636 and 3269.", 13, "#1e3a8a")]
window(W3, H3, "certlm - [Certificates - Local Computer\\Personal\\Certificates]", "".join(inner),
       "Local computer certificate store on DC01 showing certificates issued to DC01.bhry98.local by bhry98-CA01-CA with Server Authentication purpose.", "05-dc-certificate")

# 6. ldp 636
W4, H4 = 900, 520
inner = [wt(14, 62, "Connection    Browse    View    Options    Utilities    Help", 13, "#111827"),
         f'<rect x="0" y="74" width="{W4}" height="{H4 - 74}" fill="#ffffff"/>',
         f'<rect x="0" y="74" width="250" height="{H4 - 74}" fill="#f9fafb" stroke="#d1d5db"/>',
         wt(270, 104, "ld = ldap_sslinit(\"dc01.bhry98.local\", 636, 1);", 13, "#111827"),
         wt(270, 126, "Error 0 = ldap_set_option(hLdap, LDAP_OPT_PROTOCOL_VERSION, 3);", 13, "#111827"),
         wt(270, 148, "Error 0 = ldap_connect(hLdap, NULL);", 13, "#111827"),
         wt(270, 170, "Error 0 = ldap_get_option(hLdap,LDAP_OPT_SSL,(void*)&lv);", 13, "#111827"),
         wt(270, 192, "Host supports SSL, SSL cipher strength = 256 bits", 13, "#15803d", 700),
         wt(270, 214, "Established connection to dc01.bhry98.local.", 13, "#15803d", 700),
         hl(264, 176, 420, 46),
         wt(270, 236, "Retrieving base DSA information...", 13, "#111827"),
         wt(270, 258, "Getting 1 entries:", 13, "#111827"),
         wt(270, 280, "Dn: (RootDSE)", 13, "#111827"),
         wt(290, 302, "defaultNamingContext: DC=bhry98,DC=local;", 13, "#111827"),
         wt(290, 324, "dnsHostName: DC01.bhry98.local;", 13, "#111827"),
         # Connect dialog
         f'<rect x="20" y="300" width="330" height="190" fill="#ffffff" stroke="#6b7280" filter=""/>',
         f'<rect x="20" y="300" width="330" height="28" fill="#f3f4f6"/>', wt(30, 319, "Connect", 13, "#111827"),
         wt(36, 356, "Server:", 13), f'<rect x="96" y="340" width="230" height="24" fill="#fff" stroke="#6b7280"/>', wt(102, 357, "dc01.bhry98.local", 13),
         wt(36, 394, "Port:", 13), f'<rect x="96" y="378" width="60" height="24" fill="#fff" stroke="#6b7280"/>', wt(104, 395, "636", 13, "#111827", 700),
         check(180, 395, "Connectionless", False), check(180, 425, "SSL", True, True),
         hl(92, 374, 68, 32), hl(174, 408, 70, 26),
         f'<rect x="110" y="448" width="80" height="26" fill="#f9fafb" stroke="#2563eb" stroke-width="2"/>', wt(150, 466, "OK", 13, anchor="middle"),
         f'<rect x="210" y="448" width="80" height="26" fill="#f9fafb" stroke="#9ca3af"/>', wt(250, 466, "Cancel", 13, anchor="middle")]
window(W4, H4, "ldaps://dc01.bhry98.local/DC=bhry98,DC=local - Ldp", "".join(inner),
       "ldp.exe connected to dc01.bhry98.local on port 636 with SSL checked, showing 'Host supports SSL, SSL cipher strength = 256 bits'.", "06-ldp-ldaps")

print("ok")
