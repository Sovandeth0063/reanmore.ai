# Curriculum Science RAG Evaluation Digest

- **Date:** 2026-10-19
- **Status:** PASSED (>= 90%) ✅
- **Embedding Engine:** FastEmbed ONNX (BAAI/bge-small-en-v1.5, 384-dim, local CPU)
- **Vector Store:** Local Embedded Qdrant (:memory: / disk)

## 1. Executive Metrics

| Metric | Target | Measured | Result |
| :--- | :---: | :---: | :---: |
| **Retrieval Success Rate** | 100.0% | **100.0%** (30/30) | ✅ |
| **Top-1 Textbook Chapter Accuracy** | >= 90.0% | **100.0%** (30/30) | ✅ |
| **Concept Recall Rate** | >= 85.0% | **100.0%** (30/30) | ✅ |
| **Premature Leak Freedom** | 100.0% | **100.0%** (30/30) | ✅ |

## 2. Question-by-Question Evaluation Details

| ID | Unit | Question | Expected Chapter | Retrieved Chapter | Top-1 Match | Score |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| sci_01 | Living Things & Plants | Why do green plants need roots? | Plant Structure and Functions | Plant Structure and Functions | ✅ | 0.793 |
| sci_02 | Living Things & Plants | What is the job of a plant stem? | Plant Structure and Functions | Plant Structure and Functions | ✅ | 0.707 |
| sci_03 | Living Things & Plants | What do plant leaves do with sunlight? | Plant Structure and Functions | Plant Structure and Functions | ✅ | 0.755 |
| sci_04 | Living Things & Plants | What three things does a seed need to sprout? | Seed Germination and Growth | Seed Germination and Growth | ✅ | 0.823 |
| sci_05 | Living Things & Plants | Does a seed need sunlight to germinate underground? | Seed Germination and Growth | Seed Germination and Growth | ✅ | 0.836 |
| sci_06 | Animal Kingdom & Habitats | What makes an animal a vertebrate? | Major Groups of Animals | Major Groups of Animals | ✅ | 0.752 |
| sci_07 | Animal Kingdom & Habitats | How can you tell if an animal is a mammal? | Major Groups of Animals | Major Groups of Animals | ✅ | 0.679 |
| sci_08 | Animal Kingdom & Habitats | How do fish breathe underwater? | Major Groups of Animals | Major Groups of Animals | ✅ | 0.624 |
| sci_09 | Animal Kingdom & Habitats | What kind of skin do reptiles have? | Major Groups of Animals | Major Groups of Animals | ✅ | 0.677 |
| sci_10 | Animal Kingdom & Habitats | Where do amphibians live during their life? | Major Groups of Animals | Major Groups of Animals | ✅ | 0.641 |
| sci_11 | States of Matter & Changes | What are the three main states of matter? | Solids, Liquids, and Gases | Solids, Liquids, and Gases | ✅ | 0.813 |
| sci_12 | States of Matter & Changes | Why does a solid keep its shape? | Solids, Liquids, and Gases | Solids, Liquids, and Gases | ✅ | 0.691 |
| sci_13 | States of Matter & Changes | Does a liquid change its shape in a cup? | Solids, Liquids, and Gases | Solids, Liquids, and Gases | ✅ | 0.682 |
| sci_14 | States of Matter & Changes | What is the science word for an ice cube turning into liquid water? | Heating and Cooling Matter | Heating and Cooling Matter | ✅ | 0.684 |
| sci_15 | States of Matter & Changes | What is it called when water vapor cools and turns into liquid droplets? | Heating and Cooling Matter | Heating and Cooling Matter | ✅ | 0.758 |
| sci_16 | Forces, Motion & Magnets | What is a force in science? | Forces that Cause Motion | Forces that Cause Motion | ✅ | 0.730 |
| sci_17 | Forces, Motion & Magnets | Why is it harder to slide a box on rough grass than smooth ice? | Forces that Cause Motion | Forces that Cause Motion | ✅ | 0.654 |
| sci_18 | Forces, Motion & Magnets | What are the two poles of a magnet? | Properties of Magnets | Properties of Magnets | ✅ | 0.785 |
| sci_19 | Forces, Motion & Magnets | What happens when two North poles of magnets are placed close together? | Properties of Magnets | Properties of Magnets | ✅ | 0.730 |
| sci_20 | Forces, Motion & Magnets | Do magnets stick to wooden tables or plastic toys? | Properties of Magnets | Properties of Magnets | ✅ | 0.702 |
| sci_21 | Forces, Motion & Simple Machines | What invisible force pulls dropped objects toward the ground? | Earth's Gravitational Pull | Earth's Gravitational Pull | ✅ | 0.718 |
| sci_22 | Earth & Solar System | What drives the water cycle on Earth? | Stages of the Water Cycle | Stages of the Water Cycle | ✅ | 0.828 |
| sci_23 | Earth & Solar System | What are rain, snow, and hail called in the water cycle? | Stages of the Water Cycle | Stages of the Water Cycle | ✅ | 0.776 |
| sci_24 | Earth & Solar System | Why do we have day and night on Earth? | Day, Night, and Earth Rotation | Day, Night, and Earth Rotation | ✅ | 0.762 |
| sci_25 | Earth & Solar System | Which planet is closest to the Sun? | Planets in Our Solar System | Planets in Our Solar System | ✅ | 0.778 |
| sci_26 | Earth & Solar System | What is the largest planet in our solar system? | Planets in Our Solar System | Planets in Our Solar System | ✅ | 0.799 |
| sci_27 | Ecosystems & Energy | What gas do green plants absorb from the air during photosynthesis? | Photosynthesis in Green Plants | Photosynthesis in Green Plants | ✅ | 0.850 |
| sci_28 | Ecosystems & Energy | Why are green plants called producers in a food chain? | Energy Flow in Ecosystems | Energy Flow in Ecosystems | ✅ | 0.779 |
| sci_29 | Human Body & Health | How do pairs of muscles work together to move your bones? | Bones and Muscles | Bones and Muscles | ✅ | 0.807 |
| sci_30 | Human Body & Health | Where does digestion first begin in the human body? | How Digestion Works | How Digestion Works | ✅ | 0.780 |
