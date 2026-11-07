# Justificar en bloc: how the Clickedu page works

Student file → "Detall d'assistència" → icon "Justificar en bloc". The tool
`justify_absences` drives the same page.

## Pages

- List: `assignatures/assistencia.php?p=justificar_bloc&alum=<alu_id>&ini=YYYYMMDD&fi=YYYYMMDD&r=a&v=assignatures_at&mst=0|1`
  - The page's "Cercar" button posts the dates and then redirects to this URL,
    so the list is just a GET.
  - `mst=0`: only absences and lates.
  - `mst=1` (eye icon "Mostrar totes les sessions"): every session of the range,
    also "Present" and "No s'ha passat llista".
- Save: form `frm_act_justificacio_bloc`, POST to the same URL, with hidden
  `p=justificar_bloc_bd`.

## Fields of the save form

For each row `n` of the table, in page order:

- `id_<n>`: record id of the absence/late, or `0` when the session has none.
- `id_sessio_<n>`: session id, or a key `YYYY/MM/DD_HHMMSS_<subject>` for a
  session where the register was not taken.
- `abs_ret_id_<n>`: `1` absence, `2` late, empty otherwise.
- A checkbox per row: `chk_<record_id>` for an absence/late,
  `chk_sessio_<session>` for any other session. Only ticked ones are sent.

Plus `v_nom_alumne`, `r`, `mst`, `p=justificar_bloc_bd`, `alum`, the annotation
`v_anotacio`, and the submit `Guardar=Justificar seleccionats`. The
`ind_email` box ("email me a copy") is never sent. "seleccionar-los tots" in the
page only ticks every checkbox in the browser.

## Known pitfalls

- **Row numbering must match the page exactly.** A "Present" row has five cells
  (no annotation cell). An earlier version skipped rows with fewer than six
  cells, so its `_<n>` numbering drifted from the page's and the save only
  applied to the first rows. Every row with a checkbox counts.
- **An already justified row keeps `abs_ret_id=1` or `2`.** Its type comes from the
  visible label ("absència justificada"), not from that hidden field, otherwise
  it would be offered again.
- The form opens inside a table row, so an HTML parser closes it early; its
  hidden fields and the annotation are read from the raw HTML.
- Pages are ISO-8859-15; the annotation is posted in that charset.

## What the tool checks after saving

It reads the full view (`mst=1`) before and after the save. Each chosen session
must now read "absència justificada" or "retard justificat" (`results`), and
every session not chosen must have the same state as before
(`others_unchanged`). `verified` is true only if both hold.
