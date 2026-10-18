describe("Style Quiz Pick Rules", () => {
  function createQuizPicker(minRequired = 3, maxAllowed = 10) {
    const picked = new Set<string>();

    return {
      getPicked: () => new Set(picked),
      count: () => picked.size,
      toggle: (id: string) => {
        if (picked.has(id)) {
          picked.delete(id);
        } else if (picked.size < maxAllowed) {
          picked.add(id);
        }
      },
      canSubmit: () => picked.size >= minRequired,
    };
  }

  it("requires minimum 3 garment picks before user can proceed", () => {
    const picker = createQuizPicker(3);

    expect(picker.canSubmit()).toBe(false);

    picker.toggle("garment-1");
    expect(picker.canSubmit()).toBe(false);
    expect(picker.count()).toBe(1);

    picker.toggle("garment-2");
    expect(picker.canSubmit()).toBe(false);
    expect(picker.count()).toBe(2);

    picker.toggle("garment-3");
    expect(picker.canSubmit()).toBe(true);
    expect(picker.count()).toBe(3);
  });

  it("allows deselecting a picked garment and re-evaluates min requirement", () => {
    const picker = createQuizPicker(3);

    picker.toggle("garment-1");
    picker.toggle("garment-2");
    picker.toggle("garment-3");
    expect(picker.canSubmit()).toBe(true);

    // Deselect garment-2
    picker.toggle("garment-2");
    expect(picker.count()).toBe(2);
    expect(picker.canSubmit()).toBe(false);
  });

  it("caps maximum picks at 10 items", () => {
    const picker = createQuizPicker(3, 10);

    for (let i = 1; i <= 12; i++) {
      picker.toggle(`garment-${i}`);
    }

    expect(picker.count()).toBe(10);
    expect(picker.getPicked().has("garment-11")).toBe(false);
    expect(picker.getPicked().has("garment-12")).toBe(false);
  });
});
