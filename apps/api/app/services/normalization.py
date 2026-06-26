from dataclasses import dataclass


SUPPORTED_CATEGORIES = {
    "mrt",
    "bus_interchange",
    "school",
    "mall",
    "park",
    "healthcare",
    "supermarket",
    "employment_node",
    "other",
}


@dataclass(frozen=True)
class CategoryLabel:
    normalized_category: str
    confidence: float
    label_source: str
    rationale: str
    needs_review: bool


RULES = {
    "mrt": "mrt",
    "station": "mrt",
    "bus interchange": "bus_interchange",
    "school": "school",
    "primary": "school",
    "secondary": "school",
    "institution": "school",
    "mall": "mall",
    "shopping": "mall",
    "hub": "mall",
    "park": "park",
    "garden": "park",
    "hospital": "healthcare",
    "polyclinic": "healthcare",
    "health": "healthcare",
    "supermarket": "supermarket",
    "fairprice": "supermarket",
    "employment": "employment_node",
    "business": "employment_node",
}


def normalize_amenity_category(raw_category: str | None) -> CategoryLabel:
    if not raw_category:
        return CategoryLabel("other", 0.4, "rule", "Missing source category.", True)

    value = raw_category.strip().lower()
    for keyword, category in RULES.items():
        if keyword in value:
            return CategoryLabel(category, 0.95, "rule", f"Matched keyword '{keyword}'.", False)

    return CategoryLabel("other", 0.45, "rule", "No deterministic category rule matched.", True)
