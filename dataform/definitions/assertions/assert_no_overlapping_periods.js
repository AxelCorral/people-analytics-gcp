// Time constraint: an employee never has two overlapping validity periods in the same infotype.
["stg_pa0000_actions", "stg_pa0001_assignments", "stg_pa0007_work_schedules"].forEach((model) => {
  assert(`assert_no_overlap_${model.replace("stg_", "")}`, {
    tags: ["assertions", "staging"],
    description: `No overlapping validity periods per employee in ${model}`,
  }).query((ctx) => `
    SELECT a.employee_id, a.valid_from, a.valid_to, b.valid_from AS overlapping_from
    FROM ${ctx.ref(model)} AS a
    JOIN ${ctx.ref(model)} AS b
      ON a.employee_id = b.employee_id
      AND a.valid_from < b.valid_from
      AND b.valid_from <= COALESCE(a.valid_to, ${constants.OPEN_END})
  `);
});
