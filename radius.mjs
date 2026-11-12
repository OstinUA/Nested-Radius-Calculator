/**
 * Geometry model for nested rounded rectangles.
 *
 * The whole calculator rests on one invariant: a child surface inset by the
 * parent's padding keeps its corners visually concentric when its radius equals
 * the parent's radius minus that padding. These helpers are deliberately free of
 * DOM and browser APIs so the rule can be reasoned about, and unit-tested, in
 * isolation from the UI.
 */

/** Radius relationship of a concentrically nested surface. */
export const RADIUS_LIMIT = Object.freeze({ min: 0, max: 1000 });

/**
 * Coerces user input into an integer pixel value inside the supported domain.
 *
 * Numeric inputs can yield `''`, `'12.7'`, `'1e3'` or an out-of-range value, and
 * an empty field must read as zero rather than as `NaN` propagating into styles.
 */
export function toRadiusPixels(value) {
    const parsed = typeof value === 'number' ? value : Number.parseFloat(value);

    if (!Number.isFinite(parsed)) {
        return RADIUS_LIMIT.min;
    }

    return clamp(Math.round(parsed), RADIUS_LIMIT.min, RADIUS_LIMIT.max);
}

/** Restricts `value` to the inclusive `[min, max]` interval. */
export function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

/** Inner radius implied by an outer radius and a padding. */
export function innerRadiusFor(outerRadius, padding) {
    return Math.max(0, outerRadius - padding);
}

/** Outer radius implied by an inner radius and a padding. */
export function outerRadiusFor(innerRadius, padding) {
    return innerRadius + padding;
}
