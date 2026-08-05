"""
3D Molecular Visualization Module
Interactive 3D structure viewer with pharmacophore highlighting
"""

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, Lipinski
from rdkit.Chem import Draw
import base64
from io import BytesIO
from typing import Optional, Dict, List
import streamlit as st

class Molecule3DViewer:
    """3D分子结构可视化器"""

    def __init__(self):
        self.mol = None
        self.smiles = None

    def load_smiles(self, smiles: str) -> bool:
        """加载SMILES并生成3D构象"""
        try:
            self.smiles = smiles
            self.mol = Chem.MolFromSmiles(smiles)
            if self.mol is None:
                return False

            # 添加氢原子
            self.mol = Chem.AddHs(self.mol)

            # 生成3D构象
            AllChem.EmbedMolecule(self.mol, randomSeed=42)
            AllChem.MMFFOptimizeMolecule(self.mol)

            return True
        except Exception as e:
            print(f"Error loading SMILES: {e}")
            return False

    def get_py3dmol_view(self, style: str = "stick", show_surface: bool = False) -> str:
        """
        生成py3Dmol可视化HTML

        Args:
            style: 显示样式 (stick, sphere, cartoon, line)
            show_surface: 是否显示分子表面
        """
        if self.mol is None:
            return ""

        # 生成mol block
        mol_block = Chem.MolToMolBlock(self.mol)

        # py3Dmol HTML代码
        html = f"""
        <div id="molecule-viewer" style="height: 400px; width: 100%; position: relative;"></div>
        <script src="https://3Dmol.csb.pitt.edu/build/3Dmol-min.js"></script>
        <script>
        let viewer = $3Dmol.createViewer("molecule-viewer", {{
            backgroundColor: 'white'
        }});

        let moldata = `{mol_block}`;
        viewer.addModel(moldata, "mol");
        viewer.setStyle({{}}, {{{style}: {{}}}});

        {"viewer.addSurface($3Dmol.SurfaceType.VDW, {opacity: 0.7, color: 'lightblue'});" if show_surface else ""}

        viewer.zoomTo();
        viewer.zoom(1.2);
        viewer.render();
        viewer.rotate(45);
        </script>
        """
        return html

    def get_pharmacophore_highlights(self) -> Dict[str, List[int]]:
        """识别药效团特征"""
        if self.mol is None:
            return {}

        highlights = {
            'hbd': [],  # 氢键供体
            'hba': [],  # 氢键受体
            'aromatic': [],  # 芳香环
            'positive': [],  # 正电荷
            'negative': []  # 负电荷
        }

        # 氢键供体（OH, NH）
        hbd_pattern = Chem.MolFromSmarts('[#7,#8;H]')
        if hbd_pattern:
            matches = self.mol.GetSubstructMatches(hbd_pattern)
            highlights['hbd'] = [atom[0] for atom in matches]

        # 氢键受体（N, O）
        hba_pattern = Chem.MolFromSmarts('[#7,#8]')
        if hba_pattern:
            matches = self.mol.GetSubstructMatches(hba_pattern)
            highlights['hba'] = [atom[0] for atom in matches]

        # 芳香环
        aromatic_pattern = Chem.MolFromSmarts('a')
        if aromatic_pattern:
            matches = self.mol.GetSubstructMatches(aromatic_pattern)
            highlights['aromatic'] = [atom[0] for atom in matches]

        return highlights

    def get_molecular_properties(self) -> Dict:
        """计算分子性质"""
        if self.mol is None:
            return {}

        mol_no_h = Chem.RemoveHs(self.mol)

        return {
            'molecular_weight': Descriptors.MolWt(mol_no_h),
            'logp': Descriptors.MolLogP(mol_no_h),
            'tpsa': Descriptors.TPSA(mol_no_h),
            'hbd': Descriptors.NumHDonors(mol_no_h),
            'hba': Descriptors.NumHAcceptors(mol_no_h),
            'rotatable_bonds': Descriptors.NumRotatableBonds(mol_no_h),
            'aromatic_rings': Descriptors.NumAromaticRings(mol_no_h),
            'lipinski_violations': self._count_lipinski_violations(mol_no_h)
        }

    def _count_lipinski_violations(self, mol) -> int:
        """计算Lipinski五规则违反数"""
        violations = 0
        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)

        if mw > 500:
            violations += 1
        if logp > 5:
            violations += 1
        if hbd > 5:
            violations += 1
        if hba > 10:
            violations += 1

        return violations

    def render_2d_with_highlights(self, highlight_atoms: List[int] = None) -> str:
        """渲染2D结构（带高亮）"""
        if self.mol is None:
            return ""

        mol_no_h = Chem.RemoveHs(self.mol)

        img = Draw.MolToImage(
            mol_no_h,
            size=(400, 300),
            highlightAtoms=highlight_atoms if highlight_atoms else []
        )

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return img_str


def render_molecule_3d_view(smiles: str, style: str = "stick", show_surface: bool = False):
    """
    Streamlit组件：渲染3D分子视图

    Args:
        smiles: SMILES字符串
        style: 显示样式
        show_surface: 是否显示表面
    """
    viewer = Molecule3DViewer()

    if not viewer.load_smiles(smiles):
        st.error("❌ Invalid SMILES string")
        return

    # 渲染3D视图
    html_code = viewer.get_py3dmol_view(style=style, show_surface=show_surface)
    st.components.v1.html(html_code, height=450)

    # 显示分子性质
    st.markdown("#### 📊 Molecular Properties")
    props = viewer.get_molecular_properties()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("MW", f"{props['molecular_weight']:.1f} Da")
    with col2:
        st.metric("LogP", f"{props['logp']:.2f}")
    with col3:
        st.metric("TPSA", f"{props['tpsa']:.1f} Ų")
    with col4:
        violations = props['lipinski_violations']
        st.metric("Lipinski", f"{violations}/4", delta="violations" if violations > 0 else "pass")

    # 显示药效团
    st.markdown("#### 🎯 Pharmacophore Features")
    highlights = viewer.get_pharmacophore_highlights()

    pcol1, pcol2, pcol3 = st.columns(3)
    with pcol1:
        st.info(f"**H-Bond Donors:** {len(highlights['hbd'])}")
    with pcol2:
        st.info(f"**H-Bond Acceptors:** {len(highlights['hba'])}")
    with pcol3:
        st.info(f"**Aromatic Atoms:** {len(highlights['aromatic'])}")
