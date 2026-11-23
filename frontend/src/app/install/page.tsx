export default function InstallPage(){
 return <main className="install-app-shell"><section className="install-app-card">
  <img src="/pennypilot-app-icon.svg" alt="PennyPilot app icon"/>
  <p className="eyebrow">PENNYPILOT APP</p>
  <h1>Install PennyPilot on phone, Windows, or Mac</h1>
  <p>The installed app uses the same PennyPilot account and database as the website. Updates deployed from VS Code to GitHub and Vercel appear automatically when the installed app reconnects.</p>

  <h2>Windows desktop</h2>
  <ol>
   <li>Open PennyPilot in Microsoft Edge or Google Chrome.</li>
   <li>In Edge, open Settings and more, then Apps, then Install this site as an app.</li>
   <li>In Chrome, open the menu, then Cast, save and share, then Install page as app.</li>
   <li>Confirm the installation. PennyPilot can then appear in Start, the taskbar, and as a desktop shortcut.</li>
  </ol>

  <h2>Mac</h2>
  <ol>
   <li>On macOS Sonoma 14 or later, open PennyPilot in Safari.</li>
   <li>Choose File, then Add to Dock.</li>
   <li>Choose the PennyPilot name and icon, then select Add.</li>
   <li>Alternatively, open PennyPilot in Chrome and choose Install page as app.</li>
  </ol>

  <h2>iPhone or iPad</h2>
  <ol>
   <li>Open PennyPilot in Safari.</li>
   <li>Tap Share.</li>
   <li>Tap Add to Home Screen.</li>
   <li>Turn on Open as Web App, then tap Add.</li>
  </ol>

  <h2>Android</h2>
  <ol>
   <li>Open PennyPilot in Chrome.</li>
   <li>Open the browser menu.</li>
   <li>Tap Install app or Add to Home screen.</li>
   <li>Confirm installation.</li>
  </ol>

  <div className="install-app-actions"><a className="button primary" href="/">Return to PennyPilot</a></div>
  <p className="muted small">This is an installable web app, not a separate EXE or DMG download. Financial and authentication responses are never stored for offline use. Internet access is required for live account data.</p>
 </section></main>;
}