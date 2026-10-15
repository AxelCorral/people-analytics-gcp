"""Generate docs/lineage.md: Mermaid dependency graph from `dataform compile --json`.

Replaces a screenshot of the Dataform console graph (the console is not used).
"""

from __future__ import annotations

from collections import defaultdict

from common import compiled_graph, write_doc

LAYERS = [
    ("hr_raw", "raw (BigQuery, chargement)"),
    ("hr_staging", "staging (vues)"),
    ("hr_intermediate", "intermediate (tables)"),
    ("hr_marts", "marts (tables, incrémental)"),
]


def node_id(target: dict) -> str:
    return f"{target['schema']}__{target['name']}"


def main() -> None:
    graph = compiled_graph()
    nodes: dict[str, tuple[str, str, str]] = {}  # id -> (schema, name, type)
    edges: set[tuple[str, str]] = set()
    for decl in graph.get("declarations", []):
        nodes[node_id(decl["target"])] = (decl["target"]["schema"], decl["target"]["name"], "declaration")
    for table in graph["tables"]:
        nodes[node_id(table["target"])] = (table["target"]["schema"], table["target"]["name"], table["type"])
        for dep in table.get("dependencyTargets", []):
            edges.add((node_id(dep), node_id(table["target"])))

    by_layer = defaultdict(list)
    for nid, (schema, name, kind) in sorted(nodes.items()):
        by_layer[schema].append((nid, name, kind))

    lines = ["flowchart LR"]
    for schema, label in LAYERS:
        lines.append(f'  subgraph {schema}["{label}"]')
        for nid, name, kind in by_layer.get(schema, []):
            shape = f'(["{name}"])' if kind == "view" else f'[["{name}"]]' if kind == "incremental" else f'["{name}"]'
            lines.append(f"    {nid}{shape}")
        lines.append("  end")
    for src, dst in sorted(edges):
        lines.append(f"  {src} --> {dst}")

    tables = graph["tables"]
    counts = defaultdict(int)
    for t in tables:
        counts[t["type"]] += 1
    custom = [a for a in graph.get("assertions", []) if "_assertions_" not in a["target"]["name"]]
    doc = "\n".join([
        "# Graphe de dépendances Dataform",
        "",
        "Généré par `tools/lineage.py` à partir de `dataform compile --json` (la console Dataform n'est pas utilisée). "
        "Forme : rectangle = table, arrondi = vue, double bord = table incrémentale.",
        "",
        f"- {len(graph.get('declarations', []))} sources déclarées (`hr_raw`)",
        f"- {counts['view']} vues, {counts['table']} tables, {counts['incremental']} table incrémentale",
        f"- {len(graph.get('assertions', []))} assertions, dont {len(custom)} personnalisées : "
        + ", ".join(f"`{a['target']['name']}`" for a in sorted(custom, key=lambda a: a["target"]["name"])),
        "",
        "Les assertions (non représentées) sont dans `hr_assertions`.",
        "",
        "```mermaid",
        *lines,
        "```",
        "",
    ])
    path = write_doc("docs/lineage.md", doc)
    print(f"{path} : {len(nodes)} nœuds, {len(edges)} arêtes")


if __name__ == "__main__":
    main()
