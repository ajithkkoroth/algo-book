# ==========================================================
# content/lab_engine.py
# SHARED ENGINE FOR ALL CHAPTERS (Left-Aligned RadioButtons)
# ==========================================================
import ipywidgets as widgets
from IPython.display import display
import hashlib

def run_generic_grader(code, spec):
    req = spec.get("required", [])
    missing = [kw for kw in req if kw not in code]
    rows = []
    passed_count = 0
    for idx, tc in enumerate(spec["tests"], 1):
        tin, exp_str, check_vars, desc = tc[0], tc[1], tc[2], tc[3]
        call_expr = tc[4] if len(tc) > 4 else None
        if missing:
            rows.append((idx, tin, exp_str, "Missing syntax", False, f"Must use: {', '.join(missing)}"))
            continue
        ns = {"input": lambda p="": tin}
        out = []
        ns["print"] = lambda *a: out.append(" ".join(str(x) for x in a))
        try:
            exec(code, ns)
            if call_expr:
                ret_val = eval(call_expr, ns)
                ns["_ret"] = ret_val
                actual = f"{ret_val:.4f}" if (spec.get("float_tol") and isinstance(ret_val, (int, float))) else str(ret_val)
            else:
                actual = out[-1].strip() if out else "Nothing"
            vars_ok = True
            for vname, vexp in check_vars.items():
                vval = ns.get(vname)
                if spec.get("float_tol"):
                    if not isinstance(vval, (int, float)) or abs(vval - vexp) > 0.001:
                        vars_ok = False
                    else:
                        actual = f"{vval:.4f}"
                else:
                    if isinstance(vval, float) and isinstance(vexp, int):
                        vars_ok = False
                    elif vval != vexp:
                        vars_ok = False
            print_ok = True if (spec.get("float_tol") or call_expr) else (actual == exp_str)
            passed = vars_ok and print_ok
            comment = desc if passed else "Check logic & return/print value"
        except Exception as e:
            actual, passed, comment = type(e).__name__, False, str(e)
        if passed:
            passed_count += 1
        rows.append((idx, tin, exp_str, actual, passed, comment))

    tr_html = ""
    for tc_num, test_in, exp_out, act_out, passed, comment in rows:
        badge = "<span style='color:#166534; font-weight:bold;'>&#9989; PASS</span>" if passed else "<span style='color:#991b1b; font-weight:bold;'>&#10060; FAIL</span>"
        tr_html += f"<tr><td>#{tc_num}</td><td><code>{test_in}</code></td><td><code>{exp_out}</code></td><td><code>{act_out}</code></td><td>{badge}</td><td style='font-family:sans-serif;'>{comment}</td></tr>"
    table_html = f"<div class='table-scroll'><table class='test-table'><thead><tr><th>#</th><th>Input / Call</th><th>Expected</th><th>Yours</th><th>Status</th><th>Feedback</th></tr></thead><tbody>{tr_html}</tbody></table></div>"
    return (passed_count == len(spec["tests"])), passed_count, table_html

def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _svg_text(x, y, text, font_size=12, bold=False, font="Times New Roman, serif"):
    weight = "bold" if bold else "normal"
    lines = str(text).split("\n")
    if len(lines) == 1 and len(text) > 22 and " " in text:
        words = text.split(" ")
        mid = len(words) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    if len(lines) == 1:
        return f"<text x='{x}' y='{y + 4}' text-anchor='middle' font-family='{font}' font-size='{font_size}' font-weight='{weight}' fill='#000000'>{_esc(lines[0])}</text>"
    else:
        return (
            f"<text x='{x}' y='{y - 4}' text-anchor='middle' font-family='{font}' font-size='{font_size}' font-weight='{weight}' fill='#000000'>{_esc(lines[0])}</text>"
            f"<text x='{x}' y='{y + 13}' text-anchor='middle' font-family='{font}' font-size='{font_size}' font-weight='{weight}' fill='#000000'>{_esc(lines[1])}</text>"
        )

def _svg_box(cx, cy, w, h, text, is_io=True):
    if is_io:
        pts = f"{cx - w//2 + 12},{cy - h//2} {cx + w//2 + 12},{cy - h//2} {cx + w//2 - 12},{cy + h//2} {cx - w//2 - 12},{cy + h//2}"
        shape = f"<polygon points='{pts}' fill='#ffffff' stroke='#000000' stroke-width='1.3'/>"
    else:
        shape = f"<rect x='{cx - w//2}' y='{cy - h//2}' width='{w}' height='{h}' fill='#ffffff' stroke='#000000' stroke-width='1.3'/>"
    return shape + _svg_text(cx, cy, text, font_size=12)

def draw_flow(steps):
    CX = 250
    y = 16
    svg_parts = []

    for idx, step in enumerate(steps):
        kind = step[0]
        is_last = (idx == len(steps) - 1)

        if kind == "oval":
            cy = y + 18
            svg_parts.append(f"<ellipse cx='{CX}' cy='{cy}' rx='58' ry='18' fill='#ffffff' stroke='#000000' stroke-width='1.3'/>")
            svg_parts.append(_svg_text(CX, cy, step[1], font_size=12.5))
            y += 36
            if not is_last:
                svg_parts.append(f"<line x1='{CX}' y1='{y}' x2='{CX}' y2='{y+24}' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
                y += 24

        elif kind in ("io", "proc"):
            cy = y + 22
            svg_parts.append(_svg_box(CX, cy, 165, 44, step[1], is_io=(kind == "io")))
            y += 44
            if not is_last:
                svg_parts.append(f"<line x1='{CX}' y1='{y}' x2='{CX}' y2='{y+24}' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
                y += 24

        elif kind == "dec":
            cy = y + 38
            pts = f"{CX},{y} {CX+98},{cy} {CX},{y+76} {CX-98},{cy}"
            svg_parts.append(f"<polygon points='{pts}' fill='#ffffff' stroke='#000000' stroke-width='1.3'/>")
            svg_parts.append(_svg_text(CX, cy, step[1], font_size=12))
            y += 76
            if not is_last:
                svg_parts.append(f"<line x1='{CX}' y1='{y}' x2='{CX}' y2='{y+24}' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
                y += 24

        elif kind == "branch":
            cond, yes_txt, no_txt = step[1], step[2], step[3]
            d_top, d_cy, d_bot = y, y + 40, y + 80
            d_left, d_right = CX - 106, CX + 106

            pts = f"{CX},{d_top} {d_right},{d_cy} {CX},{d_bot} {d_left},{d_cy}"
            svg_parts.append(f"<polygon points='{pts}' fill='#ffffff' stroke='#000000' stroke-width='1.3'/>")
            svg_parts.append(_svg_text(CX, d_cy, cond, font_size=12))

            lx, rx = 102, 398
            box_top, box_cy, box_bot = d_cy + 62, d_cy + 87, d_cy + 112

            svg_parts.append(f"<polyline points='{d_left},{d_cy} {lx},{d_cy} {lx},{box_top}' fill='none' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
            svg_parts.append(f"<text x='{lx + 20}' y='{d_cy + 26}' font-family='Times New Roman, serif' font-size='12' fill='#000000'>Yes</text>")

            svg_parts.append(f"<polyline points='{d_right},{d_cy} {rx},{d_cy} {rx},{box_top}' fill='none' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
            svg_parts.append(f"<text x='{rx - 30}' y='{d_cy + 26}' font-family='Times New Roman, serif' font-size='12' fill='#000000'>No</text>")

            yes_is_io = any(k in yes_txt.upper() for k in ("PRINT", "DISPLAY", "READ", "INPUT", "RETURN"))
            no_is_io = any(k in no_txt.upper() for k in ("PRINT", "DISPLAY", "READ", "INPUT", "RETURN"))
            svg_parts.append(_svg_box(lx, box_cy, 148, 50, yes_txt, is_io=yes_is_io))
            svg_parts.append(_svg_box(rx, box_cy, 148, 50, no_txt, is_io=no_is_io))

            merge_y = box_bot + 16
            svg_parts.append(f"<polyline points='{lx},{box_bot} {lx},{merge_y} {rx},{merge_y} {rx},{box_bot}' fill='none' stroke='#000000' stroke-width='1.3'/>")
            y = merge_y
            if not is_last:
                svg_parts.append(f"<line x1='{CX}' y1='{y}' x2='{CX}' y2='{y+24}' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
                y += 24

        elif kind == "nested_branch":
            cond1, yes1_txt, cond2, yes2_txt, no2_txt = step[1], step[2], step[3], step[4], step[5]
            d1_top, d1_cy, d1_bot = y, y + 36, y + 72
            d1_left, d1_right = CX - 86, CX + 86
            pts1 = f"{CX},{d1_top} {d1_right},{d1_cy} {CX},{d1_bot} {d1_left},{d1_cy}"
            svg_parts.append(f"<polygon points='{pts1}' fill='#ffffff' stroke='#000000' stroke-width='1.3'/>")
            svg_parts.append(_svg_text(CX, d1_cy, cond1, font_size=11.5))

            cx2 = 345
            d2_top = d1_cy + 38
            d2_cy, d2_bot = d2_top + 36, d2_top + 72
            d2_left, d2_right = cx2 - 78, cx2 + 78

            svg_parts.append(f"<polyline points='{d1_right},{d1_cy} {cx2},{d1_cy} {cx2},{d2_top}' fill='none' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
            svg_parts.append(f"<text x='{d1_right + 14}' y='{d1_cy - 6}' font-family='Times New Roman, serif' font-size='11.5' fill='#000000'>No</text>")

            pts2 = f"{cx2},{d2_top} {d2_right},{d2_cy} {cx2},{d2_bot} {d2_left},{d2_cy}"
            svg_parts.append(f"<polygon points='{pts2}' fill='#ffffff' stroke='#000000' stroke-width='1.3'/>")
            svg_parts.append(_svg_text(cx2, d2_cy, cond2, font_size=11.5))

            x1, x2, x3 = 82, 255, 422
            box_top, box_cy, box_bot = d2_cy + 54, d2_cy + 78, d2_cy + 102

            svg_parts.append(f"<polyline points='{d1_left},{d1_cy} {x1},{d1_cy} {x1},{box_top}' fill='none' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
            svg_parts.append(f"<text x='{x1 + 18}' y='{d1_cy + 22}' font-family='Times New Roman, serif' font-size='11.5' fill='#000000'>Yes</text>")

            svg_parts.append(f"<polyline points='{d2_left},{d2_cy} {x2},{d2_cy} {x2},{box_top}' fill='none' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
            svg_parts.append(f"<text x='{x2 + 16}' y='{d2_cy + 22}' font-family='Times New Roman, serif' font-size='11.5' fill='#000000'>Yes</text>")

            svg_parts.append(f"<polyline points='{d2_right},{d2_cy} {x3},{d2_cy} {x3},{box_top}' fill='none' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
            svg_parts.append(f"<text x='{x3 - 24}' y='{d2_cy + 22}' font-family='Times New Roman, serif' font-size='11.5' fill='#000000'>No</text>")

            b1_io = any(k in yes1_txt.upper() for k in ("PRINT", "DISPLAY", "READ", "INPUT", "RETURN"))
            b2_io = any(k in yes2_txt.upper() for k in ("PRINT", "DISPLAY", "READ", "INPUT", "RETURN"))
            b3_io = any(k in no2_txt.upper() for k in ("PRINT", "DISPLAY", "READ", "INPUT", "RETURN"))

            svg_parts.append(_svg_box(x1, box_cy, 124, 48, yes1_txt, is_io=b1_io))
            svg_parts.append(_svg_box(x2, box_cy, 124, 48, yes2_txt, is_io=b2_io))
            svg_parts.append(_svg_box(x3, box_cy, 124, 48, no2_txt, is_io=b3_io))

            merge_y = box_bot + 16
            svg_parts.append(f"<polyline points='{x1},{box_bot} {x1},{merge_y} {x3},{merge_y} {x3},{box_bot}' fill='none' stroke='#000000' stroke-width='1.3'/>")
            svg_parts.append(f"<line x1='{x2}' y1='{box_bot}' x2='{x2}' y2='{merge_y}' stroke='#000000' stroke-width='1.3'/>")
            y = merge_y
            if not is_last:
                svg_parts.append(f"<line x1='{CX}' y1='{y}' x2='{CX}' y2='{y+24}' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
                y += 24

        elif kind == "loop":
            cond, body_txt = step[1], step[2]
            d_top, d_cy, d_bot = y, y + 38, y + 76
            d_left, d_right = CX - 100, CX + 100

            pts = f"{CX},{d_top} {d_right},{d_cy} {CX},{d_bot} {d_left},{d_cy}"
            svg_parts.append(f"<polygon points='{pts}' fill='#ffffff' stroke='#000000' stroke-width='1.3'/>")
            svg_parts.append(_svg_text(CX, d_cy, cond, font_size=12))

            body_top, body_cy, body_bot = d_bot + 26, d_bot + 50, d_bot + 74
            svg_parts.append(f"<line x1='{CX}' y1='{d_bot}' x2='{CX}' y2='{body_top}' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
            svg_parts.append(f"<text x='{CX + 18}' y='{d_bot + 16}' font-family='Times New Roman, serif' font-size='12' fill='#000000'>Yes</text>")

            svg_parts.append(_svg_box(CX, body_cy, 175, 48, body_txt, is_io=False))

            loop_x = 95
            svg_parts.append(f"<polyline points='{CX - 87},{body_cy} {loop_x},{body_cy} {loop_x},{d_cy} {d_left},{d_cy}' fill='none' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")

            exit_x, exit_y = 405, body_bot + 18
            svg_parts.append(f"<text x='{d_right + 16}' y='{d_cy - 6}' font-family='Times New Roman, serif' font-size='12' fill='#000000'>No</text>")
            svg_parts.append(f"<polyline points='{d_right},{d_cy} {exit_x},{d_cy} {exit_x},{exit_y} {CX},{exit_y}' fill='none' stroke='#000000' stroke-width='1.3'/>")
            y = exit_y
            if not is_last:
                svg_parts.append(f"<line x1='{CX}' y1='{y}' x2='{CX}' y2='{y+24}' stroke='#000000' stroke-width='1.3' marker-end='url(#arrow)'/>")
                y += 24

    total_h = y + 16
    return f"""
    <div class='flow-wrap'>
      <svg viewBox='0 0 500 {total_h}' style='width:100%; max-width:480px; height:auto; display:block; margin:0 auto; background:white;'>
        <defs>
          <marker id='arrow' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='6' markerHeight='6' orient='auto-start-reverse'>
            <path d='M 0 1 L 10 5 L 0 9 z' fill='#000000'/>
          </marker>
        </defs>
        {"".join(svg_parts)}
      </svg>
    </div>
    """

def launch_lab(chapter_code, chapter_title, mcq_data, pseudo_tasks, missions_spec,
               book_title="Algorithmic Thinking with Python",
               author_name="Dr. Ajith K K, Dept. of ECE, GCE Kannur"):
    NUM_MCQ = len(mcq_data)
    NUM_PSEUDO = len(pseudo_tasks)
    NUM_PY = len(missions_spec)

    state = {
        "roll_locked": False,
        "locked_roll_str": "",
        "mcq_passed": [False] * NUM_MCQ,
        "pseudo_done": [False] * NUM_PSEUDO,
        "py_passed": [False] * NUM_PY,
        "py_tc_scores": [0] * NUM_PY,
        "py_attempts": [0] * NUM_PY
    }

    header_widget = widgets.HTML(value=f"""
    <style>
      .jupyter-widgets.widget-html, .widget-html > .widget-html-content, .jp-RenderedHTMLCommon {{ height: auto !important; max-height: none !important; overflow: visible !important; }}
      .jupyter-widgets.widget-radio-box {{ display: flex !important; flex-direction: column !important; align-items: flex-start !important; justify-content: flex-start !important; width: 100% !important; height: auto !important; max-height: none !important; overflow: visible !important; margin: 6px 0 !important; padding: 0 !important; }}
      .widget-radio-box .widget-label {{ display: none !important; width: 0 !important; }}
      .widget-radio-box label {{ display: flex !important; flex-direction: row !important; align-items: flex-start !important; justify-content: flex-start !important; text-align: left !important; width: 100% !important; height: auto !important; min-height: 26px !important; line-height: 1.4 !important; margin: 0 0 8px 0 !important; padding: 0 !important; white-space: normal !important; word-break: break-word !important; font-family: sans-serif !important; font-size: 0.88rem !important; cursor: pointer; }}
      .widget-radio-box input[type="radio"] {{ margin: 3px 10px 0 2px !important; flex-shrink: 0 !important; order: -1 !important; }}
      .lab-header {{ background: linear-gradient(135deg, #1e3a8a, #1e40af); color: white; padding: 14px 18px; border-radius: 8px; margin-bottom: 8px; font-family: sans-serif; }}
      .book-badge {{ display: inline-block; background: rgba(255,255,255,0.18); color: #e0f2fe; padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }}
      .lab-header h1 {{ margin: 0 0 2px 0; font-size: 1.3rem; color: white; line-height: 1.25; }}
      .author-line {{ margin: 0; font-size: 0.85rem; color: #bfdbfe; font-weight: 600; }}
      .lm-TabBar-tab, .p-TabBar-tab, .jupyter-widgets.widget-tab > .p-TabBar .p-TabBar-tab {{ min-width: 65px !important; max-width: 125px !important; padding: 4px 8px !important; font-size: 0.8rem !important; font-family: sans-serif !important; }}
      .resp-progress-box {{ display: flex !important; flex-direction: row !important; justify-content: space-between !important; align-items: center !important; background: #e2e8f0 !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; padding: 6px 12px !important; margin: 0 0 10px 0 !important; height: auto !important; overflow: visible !important; }}
      .prog-line {{ font-family: sans-serif; font-size: 0.84rem; font-weight: 600; color: #1e293b; line-height: 1.35; white-space: nowrap; }}
      .prog-line-score {{ font-family: sans-serif; font-size: 0.85rem; font-weight: 700; color: #1e40af; line-height: 1.35; white-space: nowrap; }}
      .pseudo-compare-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 8px; }}
      @media (max-width: 640px) {{
        .resp-progress-box {{ flex-direction: column !important; align-items: flex-start !important; padding: 6px 10px !important; }}
        .pseudo-compare-grid {{ grid-template-columns: 1fr; }}
        .lab-header h1 {{ font-size: 1.15rem; }}
      }}
      .code-card {{ background: #1e293b; color: #f8fafc; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; word-break: break-word; margin: 6px 0; line-height: 1.35; }}
      .pass-box {{ background: #dcfce7; color: #166534; padding: 8px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; margin-top: 6px; border: 1px solid #86efac; font-family: sans-serif; }}
      .fail-box {{ background: #fee2e2; color: #991b1b; padding: 8px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; margin-top: 6px; border: 1px solid #fca5a5; font-family: sans-serif; }}
      .hint-box {{ background: #fef9c3; color: #854d0e; padding: 8px 10px; border-radius: 6px; font-weight: 500; font-size: 0.85rem; margin-top: 6px; border: 1px solid #fde047; font-family: sans-serif; }}
      .lock-banner {{ background: #f1f5f9; color: #475569; padding: 16px 12px; border-radius: 8px; border: 2px dashed #94a3b8; text-align: center; font-family: sans-serif; font-size: 0.9rem; margin: 8px 0; }}
      .roll-gate-banner {{ background: #eff6ff; color: #1e3a8a; padding: 14px 12px; border-radius: 8px; border: 2px solid #93c5fd; text-align: center; font-family: sans-serif; font-size: 0.9rem; margin: 6px 0; }}
      .table-scroll {{ width: 100%; overflow-x: auto; margin-top: 6px; }}
      .test-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.82rem; background: white; }}
      .test-table th {{ background: #f1f5f9; color: #1e293b; padding: 6px; border: 1px solid #cbd5e1; text-align: left; }}
      .test-table td {{ padding: 6px; border: 1px solid #cbd5e1; font-family: monospace; }}
      .stamp-banner {{ background: #dcfce7; border: 2px dashed #16a34a; color: #14532d; padding: 10px; border-radius: 8px; margin: 6px 0; font-family: sans-serif; font-size: 0.88rem; font-weight: bold; text-align: center; }}
      .flow-wrap {{ text-align: center; padding: 12px 8px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; overflow-x: auto; }}
      .lab-footer {{ text-align: center; color: #64748b; font-family: sans-serif; font-size: 0.78rem; margin-top: 14px; padding-top: 8px; border-top: 1px solid #cbd5e1; }}
    </style>
    <div class='lab-header'>
      <div class='book-badge'>{book_title}</div>
      <h1>{chapter_title}</h1>
      <div class='author-line'>{author_name}</div>
    </div>
    """)

    footer_widget = widgets.HTML(value=f"<div class='lab-footer'><strong>{book_title}</strong> &bull; {author_name}</div>")

    roll_input = widgets.Text(placeholder="e.g. 12 or 26EC012", description="Roll No:", layout=widgets.Layout(width='210px', margin='0 6px 0 0'))
    lock_roll_btn = widgets.Button(description="Lock Roll No & Start", button_style="primary", layout=widgets.Layout(width='155px', height='30px'))
    roll_status_html = widgets.HTML(value="")
    roll_bar = widgets.HBox([roll_input, lock_roll_btn], layout=widgets.Layout(align_items='center', margin='0 0 6px 0'))

    p_row1 = widgets.HTML(layout=widgets.Layout(margin='0 6px 0 0', width='auto'))
    p_row2 = widgets.HTML(layout=widgets.Layout(margin='0 6px 0 0', width='auto'))
    p_row3 = widgets.HTML(layout=widgets.Layout(margin='0 6px 0 0', width='auto'))
    p_row4 = widgets.HTML(layout=widgets.Layout(margin='0', width='auto'))
    progress_box = widgets.Box([p_row1, p_row2, p_row3, p_row4], layout=widgets.Layout(width='99%'))
    progress_box.add_class("resp-progress-box")

    stamp_box = widgets.HTML(value="")
    workspace_container = widgets.VBox()
    roll_gate_msg = widgets.HTML(value="<div class='roll-gate-banner'>&#128272; <strong>Step 1: Enter &amp; Lock Your Roll Number Above!</strong><br>Your Roll Number will be locked for this session to generate your Verification Stamp.</div>")

    tabs = widgets.Tab(layout=widgets.Layout(width='99%', margin='4px 0 0 0'))
    stage2_container, stage3_container = widgets.VBox(), widgets.VBox()
    stage2_content, stage3_content = widgets.VBox(), widgets.VBox()

    stage2_lock_msg = widgets.HTML(value=f"<div class='lock-banner'>&#128274; <strong>Stage 2 Locked!</strong> Complete all {NUM_MCQ} MCQs in Tab 1 first.</div>")
    stage3_lock_msg = widgets.HTML(value=f"<div class='lock-banner'>&#128274; <strong>Stage 3 Locked!</strong> Complete all {NUM_PSEUDO} Pseudocode tasks in Tab 2 first.</div>")

    def refresh_progress(auto_switch=False):
        m_done = sum(state["mcq_passed"])
        p_done = sum(state["pseudo_done"])
        c_done = sum(state["py_passed"])
        tc_done = sum(state["py_tc_scores"])
        max_tc = sum(len(m["tests"]) for m in missions_spec)

        total_score = m_done * 1 + p_done * 2 + tc_done
        max_score = NUM_MCQ * 1 + NUM_PSEUDO * 2 + max_tc

        s1_icon = "&#9989;" if m_done == NUM_MCQ else "&#9203;"
        s2_icon = "&#9989;" if p_done == NUM_PSEUDO else ("&#9203;" if m_done == NUM_MCQ else "&#128274;")
        s3_icon = "&#9989;" if c_done == NUM_PY else ("&#9203;" if p_done == NUM_PSEUDO else "&#128274;")

        p_row1.value = f"<div class='prog-line'>{s1_icon} Stage 1 (MCQs): {m_done}/{NUM_MCQ}</div>"
        p_row2.value = f"<div class='prog-line'>{s2_icon} Stage 2 (Pseudocode): {p_done}/{NUM_PSEUDO}</div>"
        p_row3.value = f"<div class='prog-line'>{s3_icon} Stage 3 (Python): {c_done}/{NUM_PY} ({tc_done}/{max_tc} Tests)</div>"
        p_row4.value = f"<div class='prog-line-score'>&#127942; Score: {total_score}/{max_score}</div>"

        tabs.set_title(0, f"1. MCQs ({m_done}/{NUM_MCQ})")
        if m_done == NUM_MCQ:
            stage2_container.children = [stage2_content]
            tabs.set_title(1, f"2. Pseudocode ({p_done}/{NUM_PSEUDO})")
            if auto_switch and p_done == 0 and tabs.selected_index == 0:
                tabs.selected_index = 1
        else:
            stage2_container.children = [stage2_lock_msg]
            tabs.set_title(1, "🔒 2. Pseudocode")

        if m_done == NUM_MCQ and p_done == NUM_PSEUDO:
            stage3_container.children = [stage3_content]
            tabs.set_title(2, f"3. Python ({c_done}/{NUM_PY})")
            if auto_switch and c_done == 0 and tabs.selected_index == 1:
                tabs.selected_index = 2
        else:
            stage3_container.children = [stage3_lock_msg]
            tabs.set_title(2, "🔒 3. Python")

        if c_done == NUM_PY and state["roll_locked"]:
            r = state["locked_roll_str"]
            secret_input = f"GCEK-ECE-2026::{r}::{chapter_code}::{total_score}"
            digest = hashlib.sha256(secret_input.encode("utf-8")).hexdigest().upper()
            pin_hash = digest[7:12]
            suffix = r[-3:] if len(r) >= 3 else r
            chap_num = chapter_code.replace("CH", "")
            stamp_box.value = (
                f"<div class='stamp-banner'>"
                f"&#127881; <strong>Chapter {chap_num} Mastered!</strong> (Roll No: {r} &bull; Score: {total_score}/{max_score})<br>"
                f"<span style='font-weight:normal; color:#166534;'>Write this verification code in your book:</span> "
                f"<span style='background:#ffffff; color:#1e40af; padding:2px 8px; border-radius:4px; border:1px solid #86efac; font-family:monospace; font-size:0.95rem;'>{chapter_code}-{suffix}-{pin_hash}</span>"
                f"</div>"
            )
    def on_lock_roll(_):
        val = roll_input.value.strip().upper()
        if len(val) < 1:
            roll_status_html.value = "<div class='fail-box' style='margin:0 0 6px 0;'>Please enter your Roll Number before locking!</div>"
            return
        state["roll_locked"] = True
        state["locked_roll_str"] = val
        roll_input.value = val
        roll_input.disabled = True
        lock_roll_btn.disabled = True
        lock_roll_btn.description = "🔒 Roll No Locked"
        roll_status_html.value = ""
        workspace_container.children = [tabs]
        refresh_progress(False)

    lock_roll_btn.on_click(on_lock_roll)

    mcq_cards = []
    for idx, q in enumerate(mcq_data):
        h = f"<h4 style='margin:0 0 4px 0; font-family:sans-serif;'>{q['title']}</h4><p style='margin:0 0 6px 0; font-family:sans-serif; font-size:0.9rem;'>{q['prompt']}</p>"
        if q.get('code'):
            h += f"<div class='code-card'>{q['code']}</div>"
        rb = widgets.RadioButtons(
            options=q['options'],
            value=None,
            style={'description_width': '0px'},
            layout=widgets.Layout(width='100%', height='auto', margin='4px 0')
        )
        btn = widgets.Button(description="Check", button_style="primary", layout=widgets.Layout(width='110px', height='32px'))
        fb_html = widgets.HTML(value="")

        def make_mcq_cb(i=idx, r=rb, fb=fb_html, item=q):
            def _cb(b):
                if r.value is None:
                    fb.value = "<div class='fail-box'>Select an option first!</div>"
                elif r.value == item['correct']:
                    state["mcq_passed"][i] = True
                    fb.value = f"<div class='pass-box'>&#9989; {item['feedback'][r.value]}</div>"
                    refresh_progress(auto_switch=True)
                else:
                    fb.value = f"<div class='fail-box'>&#10060; {item['feedback'][r.value]}</div>"
            return _cb

        btn.on_click(make_mcq_cb())
        mcq_cards.append(widgets.VBox(
            [widgets.HTML(value=h), rb, btn, fb_html],
            layout=widgets.Layout(border='1px solid #cbd5e1', padding='10px', margin='0 0 10px 0', align_items='flex-start')
        ))

    stage1_container = widgets.VBox(mcq_cards)

    pseudo_cards = []
    for idx, p in enumerate(pseudo_tasks):
        ta = widgets.Textarea(placeholder="START\n...", layout=widgets.Layout(width='98%', height='95px'))
        btn = widgets.Button(description="Compare Flowchart", button_style="primary", layout=widgets.Layout(width='160px', height='32px'))
        fb_html = widgets.HTML(value="")

        def make_p_cb(i=idx, t=ta, fb=fb_html, item=p):
            def _cb(b):
                val = t.value.strip()
                if len(val) < 12:
                    fb.value = "<div class='fail-box'>Write your complete pseudocode steps first!</div>"
                    return
                state["pseudo_done"][i] = True
                f_html = draw_flow(item['flow'])
                fb.value = f"<div class='pass-box'>&#9989; Submitted! Compare below:</div><div class='pseudo-compare-grid'><div><strong style='font-family:sans-serif; font-size:0.82rem;'>Your Pseudocode:</strong><div class='code-card'>{val}</div></div><div><strong style='font-family:sans-serif; font-size:0.82rem;'>Instructor Model:</strong><div class='code-card'>{item['model']}</div></div></div><strong style='font-family:sans-serif; font-size:0.82rem;'>Flowchart:</strong>{f_html}"
                refresh_progress(auto_switch=True)
            return _cb

        btn.on_click(make_p_cb())
        pseudo_cards.append(widgets.VBox([widgets.HTML(value=f"<h4 style='margin:0 0 4px 0; font-family:sans-serif;'>{p['title']}</h4><p style='margin:0 0 6px 0; font-family:sans-serif; font-size:0.9rem;'>{p['prompt']}</p>"), ta, btn, fb_html], layout=widgets.Layout(border='1px solid #cbd5e1', padding='10px', margin='0 0 10px 0')))

    stage2_content.children = pseudo_cards

    py_cards = []
    for idx, m in enumerate(missions_spec):
        ta = widgets.Textarea(value=m['starter'], layout=widgets.Layout(width='98%', height='105px'))
        btn = widgets.Button(description="Run Test Cases", button_style="success", layout=widgets.Layout(width='150px', height='32px'))
        fb = widgets.HTML(value="")

        def make_cb(i=idx, t=ta, f=fb, spec=m):
            def _cb(_):
                state["py_attempts"][i] += 1
                ok, tc_passed, table_html = run_generic_grader(t.value, spec)
                state["py_passed"][i] = ok
                state["py_tc_scores"][i] = tc_passed
                tot = len(spec['tests'])
                banner = f"<div class='pass-box'>&#9989; PASSED ({tc_passed}/{tot})!</div>" if ok else f"<div class='fail-box'>&#10060; {tc_passed}/{tot} Passed:</div>"
                hint_html = f"<div class='hint-box'>&#128161; <strong>Hint:</strong> {spec['hint']}</div>" if (not ok and state["py_attempts"][i] >= 2) else ""
                f.value = banner + table_html + hint_html
                refresh_progress(auto_switch=False)
            return _cb

        btn.on_click(make_cb())
        py_cards.append(widgets.VBox([widgets.HTML(value=f"<h4 style='margin:0 0 4px 0; font-family:sans-serif;'>{m['title']}</h4><p style='margin:0 0 6px 0; font-family:sans-serif; font-size:0.9rem;'>{m['prompt']}</p>"), ta, btn, fb], layout=widgets.Layout(border='1px solid #cbd5e1', padding='10px', margin='0 0 10px 0')))

    stage3_content.children = py_cards

    tabs.children = [stage1_container, stage2_container, stage3_container]
    workspace_container.children = [roll_gate_msg]
    refresh_progress(auto_switch=False)

    display(widgets.VBox([header_widget, roll_bar, roll_status_html, progress_box, stamp_box, workspace_container, footer_widget]))
