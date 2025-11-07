import { useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';

export default function App() {
  const [folder, setFolder] = useState('');
  const [assets, setAssets] = useState([]);

  const handleList = async () => {
    if (!folder) return;
    const entries = await invoke('list_assets', { path: folder });
    setAssets(entries);
  };

  return (
    <div className="app">
      <header>
        <h1>Audiodescrição Toolkit (Desktop)</h1>
        <p>Arraste arquivos, monitore progresso e visualize os artefatos gerados.</p>
      </header>
      <section>
        <label>
          Pasta de saída
          <input value={folder} onChange={(event) => setFolder(event.target.value)} placeholder="/Users/voce/outputs" />
        </label>
        <button onClick={handleList}>Listar artefatos</button>
      </section>
      <section className="assets">
        <h2>Arquivos disponíveis</h2>
        <ul>
          {assets.map((asset) => (
            <li key={asset.path}>
              <span>{asset.name}</span>
              <code>{asset.path}</code>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
