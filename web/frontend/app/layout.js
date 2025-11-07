import './globals.css';

export const metadata = {
  title: 'Audiodescrição Toolkit',
  description: 'Gerador de audiodescrição brasileira',
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body className="bg-slate-950 text-slate-100">{children}</body>
    </html>
  );
}
